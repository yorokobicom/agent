package wizard

import (
    "fmt"
    "os/exec"
    "strings"

    "yorokobi-agent/pkg/config"
    "yorokobi-agent/pkg/logging"
    "yorokobi-agent/pkg/system"
)

type DatabaseInfo struct {
    Type    string
    Version string
    Path    string
    Include bool
}

type BackupWizard struct {
    logger     logging.Logger
    databases  []DatabaseInfo
    paths      map[string]bool  // path -> include
}

func NewBackupWizard(logger logging.Logger) *BackupWizard {
    return &BackupWizard{
        logger: logger,
        paths: map[string]bool{
            "/etc":           true,
            "/home":         true,
            "/root":         true,
            "/var/www":      true,
            "/usr/local/bin": true,
        },
    }
}

func (w *BackupWizard) Run() (*config.BackupConfig, error) {
    // Check and install system dependencies first
    checker := system.NewSystemChecker(w.logger)
    if err := checker.CheckAndInstall(); err != nil {
        return nil, fmt.Errorf("system setup failed: %v", err)
    }

    fmt.Println("Welcome to the Backup Configuration Wizard!")
    
    // Ask for restic repository
    repository := w.promptString("Enter restic repository location (e.g., /path/to/backup, s3:bucket-name):")
    if repository == "" {
        return nil, fmt.Errorf("repository location is required")
    }

    // Ask for restic password
    password := w.promptString("Enter restic repository password:")
    if password == "" {
        return nil, fmt.Errorf("repository password is required")
    }

    // 1. Detect databases
    if err := w.detectDatabases(); err != nil {
        return nil, fmt.Errorf("database detection failed: %v", err)
    }

    // 2. Ask user about detected databases
    if len(w.databases) > 0 {
        fmt.Println("\nDetected databases:")
        for i, db := range w.databases {
            fmt.Printf("[%d] %s (version: %s) at %s\n", i+1, db.Type, db.Version, db.Path)
            w.databases[i].Include = w.promptYesNo(fmt.Sprintf("Include %s in backups?", db.Type))
        }
    }

    // 3. Show and confirm default paths
    fmt.Println("\nDefault backup paths:")
    for path := range w.paths {
        w.paths[path] = w.promptYesNo(fmt.Sprintf("Include %s in backups?", path))
    }

    // 4. Ask for additional paths
    for {
        if !w.promptYesNo("Would you like to add another path?") {
            break
        }
        path := w.promptString("Enter the path:")
        if path != "" {
            w.paths[path] = true
        }
    }

    // 5. Create backup config
    cfg := &config.BackupConfig{
        Repository: repository,
        Password:   password,
        Paths:     make([]string, 0),
        Databases: make([]config.DatabaseBackupConfig, 0),
        Schedule:  "24h",
    }

    // Add selected paths
    for path, include := range w.paths {
        if include {
            cfg.Paths = append(cfg.Paths, path)
        }
    }

    // Add selected databases
    for _, db := range w.databases {
        if db.Include {
            cfg.Databases = append(cfg.Databases, config.DatabaseBackupConfig{
                Type:    db.Type,
                Path:    db.Path,
                Version: db.Version,
            })
        }
    }

    return cfg, nil
}

func (w *BackupWizard) detectDatabases() error {
    // Detect PostgreSQL
    if version, path, err := w.detectPostgres(); err == nil {
        w.databases = append(w.databases, DatabaseInfo{
            Type:    "postgresql",
            Version: version,
            Path:    path,
            Include: true,
        })
    }

    // Detect MySQL/MariaDB
    if version, path, err := w.detectMysql(); err == nil {
        w.databases = append(w.databases, DatabaseInfo{
            Type:    "mysql",
            Version: version,
            Path:    path,
            Include: true,
        })
    }

    // Detect Redis
    if version, path, err := w.detectRedis(); err == nil {
        w.databases = append(w.databases, DatabaseInfo{
            Type:    "redis",
            Version: version,
            Path:    path,
            Include: true,
        })
    }

    return nil
}

func (w *BackupWizard) detectPostgres() (string, string, error) {
    cmd := exec.Command("psql", "--version")
    out, err := cmd.Output()
    if err != nil {
        return "", "", err
    }

    // Parse version from output
    version := strings.TrimSpace(string(out))
    
    // Try to find data directory
    dataDir := "/var/lib/postgresql"
    if _, err := exec.Command("pg_config", "--data-directory").Output(); err == nil {
        dataDir = strings.TrimSpace(string(out))
    }

    return version, dataDir, nil
}

func (w *BackupWizard) detectMysql() (string, string, error) {
    // Try mysql --version
    cmd := exec.Command("mysql", "--version")
    out, err := cmd.Output()
    if err != nil {
        return "", "", err
    }

    // Parse version from output
    version := strings.TrimSpace(string(out))
    
    // Default data directory for MySQL/MariaDB
    dataDir := "/var/lib/mysql"
    
    // Try to get actual data directory (might need sudo)
    cmd = exec.Command("mysql", "-N", "-B", "-e", "SELECT @@datadir;")
    if dirOut, err := cmd.Output(); err == nil {
        dataDir = strings.TrimSpace(string(dirOut))
    }

    return version, dataDir, nil
}

func (w *BackupWizard) detectRedis() (string, string, error) {
    // Try redis-cli --version
    cmd := exec.Command("redis-cli", "--version")
    out, err := cmd.Output()
    if err != nil {
        return "", "", err
    }

    // Parse version from output
    version := strings.TrimSpace(string(out))
    
    // Default Redis data directory
    dataDir := "/var/lib/redis"
    
    // Try to get actual data directory from redis-cli info
    cmd = exec.Command("redis-cli", "info", "server")
    if infoOut, err := cmd.Output(); err == nil {
        // Parse the info output to find dir
        info := string(infoOut)
        for _, line := range strings.Split(info, "\n") {
            if strings.HasPrefix(line, "dir:") {
                dataDir = strings.TrimSpace(strings.TrimPrefix(line, "dir:"))
                break
            }
        }
    }

    return version, dataDir, nil
}

func (w *BackupWizard) promptYesNo(question string) bool {
    var response string
    fmt.Printf("%s (y/n): ", question)
    fmt.Scanln(&response)
    return strings.ToLower(response) == "y"
}

func (w *BackupWizard) promptString(prompt string) string {
    var response string
    fmt.Printf("%s: ", prompt)
    fmt.Scanln(&response)
    return response
} 