package backups

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"

	"yorokobi-agent/pkg/config"
	"yorokobi-agent/pkg/logging"
)

var execCommand = exec.Command

type ResticBackuper struct {
	config *config.BackupConfig
	logger logging.Logger
}

func NewResticBackuper(config *config.BackupConfig, logger logging.Logger) *ResticBackuper {
	r := &ResticBackuper{
		config: config,
		logger: logger,
	}

	// Validate config
	if config.Repository == "" {
		logger.Fatalf("No repository configured. Please run 'agent setup' first")
	}
	if config.Password == "" {
		logger.Fatalf("No repository password configured. Please run 'agent setup' first")
	}

	// Initialize restic repository if needed
	logger.Info("Checking restic repository...")
	cmd := execCommand("restic", "snapshots")
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("RESTIC_REPOSITORY=%s", config.Repository),
		fmt.Sprintf("RESTIC_PASSWORD=%s", config.Password))

	if out, err := cmd.CombinedOutput(); err != nil {
		logger.Info("Repository not initialized, attempting to initialize...")
		initCmd := execCommand("restic", "init")
		initCmd.Env = cmd.Env
		if out, err := initCmd.CombinedOutput(); err != nil {
			logger.Fatalf("Failed to initialize repository: %v\nOutput: %s", err, string(out))
		}
		logger.Info("Repository initialized successfully")
	} else {
		logger.Info("Repository exists and is accessible")
		logger.Info(string(out)) // Show existing snapshots
	}

	return r
}

func (r *ResticBackuper) Backup() error {
	r.logger.Info("Starting backup...")
	startTime := time.Now()

	// Set environment variables for restic
	env := append(os.Environ(),
		fmt.Sprintf("RESTIC_REPOSITORY=%s", r.config.Repository),
		fmt.Sprintf("RESTIC_PASSWORD=%s", r.config.Password))

	// 1. First, backup databases if configured
	for _, db := range r.config.Databases {
		r.logger.Info(fmt.Sprintf("Starting backup of %s database...", db.Type))
		if err := r.backupDatabase(db, env); err != nil {
			r.logger.Errorf("Failed to backup database %s: %v", db.Type, err)
			continue
		}
		r.logger.Info(fmt.Sprintf("Completed backup of %s database", db.Type))
	}

	// 2. Backup configured paths
	for _, path := range r.config.Paths {
		r.logger.Info(fmt.Sprintf("Starting backup of path: %s", path))
		if err := r.backupPath(path, env); err != nil {
			r.logger.Errorf("Failed to backup path %s: %v", path, err)
			continue
		}
		r.logger.Info(fmt.Sprintf("Completed backup of path: %s", path))
	}

	r.logger.Info(fmt.Sprintf("Backup completed in %v", time.Since(startTime)))
	return nil
}

func (r *ResticBackuper) backupDatabase(db config.DatabaseBackupConfig, env []string) error {
	r.logger.Info(fmt.Sprintf("Creating dump for %s database...", db.Type))

	tmpDir := fmt.Sprintf("/tmp/yorokobi-backup-%s-%d", db.Type, time.Now().Unix())
	if err := os.MkdirAll(tmpDir, 0755); err != nil {
		return fmt.Errorf("failed to create temp directory: %v", err)
	}

	switch db.Type {
	case "postgresql":
		r.logger.Info("Listing all PostgreSQL databases...")
		listCmd := execCommand("psql", "-t", "-c", "SELECT datname FROM pg_database WHERE datistemplate = false;")
		out, err := listCmd.CombinedOutput()
		if err != nil {
			return fmt.Errorf("failed to list PostgreSQL databases: %v\nOutput: %s", err, string(out))
		}

		databases := strings.Split(strings.TrimSpace(string(out)), "\n")
		for _, dbName := range databases {
			dbName = strings.TrimSpace(dbName)
			if dbName == "" {
				continue
			}

			dumpFile := fmt.Sprintf("%s/%s.dump", tmpDir, dbName)
			r.logger.Info(fmt.Sprintf("Running pg_dump for database: %s", dbName))
			cmd := execCommand("pg_dump", "-Fc", "-f", dumpFile, dbName)
			if o, e := cmd.CombinedOutput(); e != nil {
				return fmt.Errorf("pg_dump failed for %s: %v\nOutput: %s", dbName, e, string(o))
			}
		}
	case "mysql":
		r.logger.Info("Running mysqldump...")
		dumpFile := fmt.Sprintf("%s/all_databases.sql", tmpDir)
		cmd := execCommand("mysqldump", "--all-databases", "-r", dumpFile)
		if out, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("mysqldump failed: %v\nOutput: %s", err, string(out))
		}
	case "redis":
		r.logger.Info("Running redis SAVE...")
		saveCmd := execCommand("redis-cli", "SAVE")
		if out, err := saveCmd.CombinedOutput(); err != nil {
			return fmt.Errorf("redis SAVE failed: %v\nOutput: %s", err, string(out))
		}

		configCmd := execCommand("redis-cli", "CONFIG", "GET", "dir")
		out, err := configCmd.CombinedOutput()
		if err != nil {
			return fmt.Errorf("failed to get Redis dir: %v\nOutput: %s", err, string(out))
		}

		lines := strings.Split(string(out), "\n")
		if len(lines) < 2 {
			return fmt.Errorf("unexpected redis-cli CONFIG GET dir output: %s", string(out))
		}

		redisDir := strings.TrimSpace(lines[1])
		if redisDir == "" {
			redisDir = "/var/lib/redis"
		}

		dumpRdb := fmt.Sprintf("%s/dump.rdb", redisDir)
		if _, err := os.Stat(dumpRdb); os.IsNotExist(err) {
			return fmt.Errorf("dump.rdb not found at %s", dumpRdb)
		}

		copyCmd := execCommand("cp", dumpRdb, fmt.Sprintf("%s/dump.rdb", tmpDir))
		if out, err := copyCmd.CombinedOutput(); err != nil {
			return fmt.Errorf("failed to copy Redis dump: %v\nOutput: %s", err, string(out))
		}
	}

	r.logger.Info("Running restic backup for database dump...")
	resticCmd := execCommand("restic", "backup", tmpDir)
	resticCmd.Env = env
	if out, err := resticCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("restic backup failed: %v\nOutput: %s", err, string(out))
	}

	defer os.RemoveAll(tmpDir)
	return nil
}

func (r *ResticBackuper) backupPath(path string, env []string) error {
	r.logger.Info(fmt.Sprintf("Running restic backup for path: %s", path))
	cmd := execCommand("restic", "backup", path)
	cmd.Env = env
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("restic backup failed for %s: %v\nOutput: %s", path, err, string(out))
	}
	return nil
}

func (r *ResticBackuper) Restore(snapshotID string, targetPath string) error {
	r.logger.Info("Starting restore...")
	startTime := time.Now()

	// Set environment variables for restic
	env := append(os.Environ(),
		fmt.Sprintf("RESTIC_REPOSITORY=%s", r.config.Repository),
		fmt.Sprintf("RESTIC_PASSWORD=%s", r.config.Password))

	// Run restic restore command
	r.logger.Info(fmt.Sprintf("Restoring snapshot %s to %s...", snapshotID, targetPath))
	restoreCmd := execCommand("restic", "restore", snapshotID, "--target", targetPath)
	restoreCmd.Env = env

	if out, err := restoreCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("restic restore failed: %v\nOutput: %s", err, string(out))
	}

	r.logger.Info(fmt.Sprintf("Restore completed in %v", time.Since(startTime)))
	return nil
}

type Snapshot struct {
	ID       string
	Time     time.Time
	Paths    []string
	Size     string
	Hostname string
}

func (r *ResticBackuper) ListSnapshots() ([]Snapshot, error) {
	cmd := execCommand("restic", "snapshots", "--json")
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("RESTIC_REPOSITORY=%s", r.config.Repository),
		fmt.Sprintf("RESTIC_PASSWORD=%s", r.config.Password))

	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list snapshots: %v", err)
	}

	var snapshots []Snapshot
	if err := json.Unmarshal(out, &snapshots); err != nil {
		return nil, fmt.Errorf("failed to parse snapshots: %v", err)
	}

	return snapshots, nil
}
