package backups

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"yorokobi-agent/pkg/config"
	"yorokobi-agent/pkg/logging"
)

// createFakeCommand creates a temporary script that simulates a command
func createFakeCommand(t *testing.T, output string, exitCode int) string {
	dir := t.TempDir()
	script := filepath.Join(dir, "fake-command")

	content := []byte(`#!/bin/sh
echo "` + output + `"
exit ` + fmt.Sprint(exitCode))

	if err := os.WriteFile(script, content, 0755); err != nil {
		t.Fatal(err)
	}
	return script
}

func TestNewResticBackuper(t *testing.T) {
	origExecCommand := execCommand
	defer func() { execCommand = origExecCommand }()

	tests := []struct {
		name         string
		config       *config.BackupConfig
		mockCommand  func(name string, args ...string) *exec.Cmd
		expectError  bool
		expectedLogs []string
	}{
		{
			name: "valid config",
			config: &config.BackupConfig{
				Repository: "/tmp/test-repo",
				Password:   "test-password",
			},
			mockCommand: func(name string, args ...string) *exec.Cmd {
				return exec.Command("true")
			},
			expectError:  false,
			expectedLogs: []string{"Checking restic repository..."},
		},
		{
			name: "missing repository",
			config: &config.BackupConfig{
				Password: "test-password",
			},
			mockCommand: func(name string, args ...string) *exec.Cmd {
				return exec.Command("false")
			},
			expectError:  true,
			expectedLogs: []string{"No repository configured"},
		},
		{
			name: "missing password",
			config: &config.BackupConfig{
				Repository: "/tmp/test-repo",
			},
			mockCommand: func(name string, args ...string) *exec.Cmd {
				return exec.Command("false")
			},
			expectError:  true,
			expectedLogs: []string{"No repository password configured"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			execCommand = tt.mockCommand
			logger := &logging.MockLogger{} // Create directly to avoid initialization

			var fatalCalled bool
			logger.FatalfFunc = func(format string, args ...interface{}) {
				fatalCalled = true
				// Store the fatal message in logs for checking
				logger.Info(fmt.Sprintf(format, args...))
			}

			_ = NewResticBackuper(tt.config, logger)

			if tt.expectError && !fatalCalled {
				t.Error("expected Fatalf to be called, but it wasn't")
			}
			if !tt.expectError && fatalCalled {
				t.Error("Fatalf was called unexpectedly")
			}

			logs := logger.GetLogs()
			for _, expectedLog := range tt.expectedLogs {
				found := false
				for _, log := range logs {
					if strings.Contains(log.Message, expectedLog) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("expected log message not found: %s\nGot logs: %v", expectedLog, logs)
				}
			}
		})
	}
}

func TestBackupDatabase(t *testing.T) {
	origExecCommand := execCommand
	defer func() { execCommand = origExecCommand }()

	// Create a temporary Redis dump file
	tmpDir := t.TempDir()
	redisDir := filepath.Join(tmpDir, "redis")
	if err := os.MkdirAll(redisDir, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(redisDir, "dump.rdb"), []byte("test"), 0644); err != nil {
		t.Fatal(err)
	}

	tests := []struct {
		name        string
		dbConfig    config.DatabaseBackupConfig
		mockCmd     func(name string, args ...string) *exec.Cmd
		expectError bool
	}{
		{
			name: "postgresql backup",
			dbConfig: config.DatabaseBackupConfig{
				Type: "postgresql",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				switch name {
				case "psql":
					return exec.Command("echo", "db1\ndb2\ndb3")
				case "pg_dump":
					return exec.Command("true")
				case "restic":
					return exec.Command("true")
				default:
					return exec.Command("true")
				}
			},
			expectError: false,
		},
		{
			name: "redis backup",
			dbConfig: config.DatabaseBackupConfig{
				Type: "redis",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				switch name {
				case "redis-cli":
					if len(args) > 0 && args[0] == "CONFIG" {
						return exec.Command("echo", "dir\n"+redisDir)
					}
					return exec.Command("true")
				case "cp":
					return exec.Command("true")
				case "restic":
					return exec.Command("true")
				default:
					return exec.Command("true")
				}
			},
			expectError: false,
		},
		{
			name: "mysql backup",
			dbConfig: config.DatabaseBackupConfig{
				Type: "mysql",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				switch name {
				case "mysqldump":
					return exec.Command("echo", "mysql dump")
				case "restic":
					return exec.Command("true")
				default:
					return exec.Command("true")
				}
			},
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			logger := logging.NewMockLogger()
			backuper := &ResticBackuper{
				config: &config.BackupConfig{
					Repository: "/tmp/test-repo",
					Password:   "test-password",
				},
				logger: logger,
			}

			execCommand = tt.mockCmd
			err := backuper.backupDatabase(tt.dbConfig, []string{
				"RESTIC_REPOSITORY=/tmp/test-repo",
				"RESTIC_PASSWORD=test-password",
			})

			if (err != nil) != tt.expectError {
				t.Errorf("backupDatabase() error = %v, expectError %v", err, tt.expectError)
			}

			// Verify logs were created
			logs := logger.GetLogs()
			if len(logs) == 0 {
				t.Error("no logs were recorded")
			}
		})
	}
}
