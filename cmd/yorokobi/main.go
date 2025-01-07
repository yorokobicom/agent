package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"yorokobi-agent/pkg/backups"
	"yorokobi-agent/pkg/config"
	"yorokobi-agent/pkg/logging"
	"yorokobi-agent/pkg/wizard"
)

const helpText = `
Yorokobi Backup Agent

Usage:
    yorokobi <command> [options]

Commands:
    setup     Configure backup settings and initialize repository
    backup    Run a one-time backup
    start     Start the backup daemon in the background
    help      Show this help message

For more information about a command:
    yorokobi help <command>
`

func main() {
	// Load config first as it's needed for all commands
	cfg, err := config.LoadConfig("config.yaml")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize logger
	logger := logging.NewLogger(&logging.Config{
		Level: cfg.Logging.Level,
	})

	if len(os.Args) < 2 || os.Args[1] == "help" || os.Args[1] == "-h" || os.Args[1] == "--help" {
		if len(os.Args) == 2 && os.Args[1] == "help" {
			showCommandHelp()
			return
		}
		fmt.Print(helpText)
		return
	}

	// Handle commands
	switch os.Args[1] {
	case "setup":
		runSetup(cfg, logger)
	case "backup":
		runBackup(cfg, logger)
	case "start":
		runDaemon(cfg, logger)
	default:
		fmt.Printf("Unknown command: %s\nRun 'yorokobi help' for usage.\n", os.Args[1])
		os.Exit(1)
	}
}

func runSetup(cfg *config.Config, logger logging.Logger) {
	w := wizard.NewBackupWizard(logger)
	backupConfig, err := w.Run()
	if err != nil {
		logger.Fatalf("Wizard failed: %v", err)
	}

	cfg.BackupConfig = *backupConfig
	if err := cfg.Save(); err != nil {
		logger.Fatalf("Failed to save config: %v", err)
	}
}

func runBackup(cfg *config.Config, logger logging.Logger) {
	backuper := backups.NewResticBackuper(&cfg.BackupConfig, logger)
	if err := backuper.Backup(); err != nil {
		logger.Fatalf("Backup failed: %v", err)
	}
}

func runDaemon(cfg *config.Config, logger logging.Logger) {
	backuper := backups.NewResticBackuper(&cfg.BackupConfig, logger)

	// Parse schedule duration
	schedule, err := time.ParseDuration(cfg.BackupConfig.Schedule)
	if err != nil {
		schedule = 24 * time.Hour // Default to daily if invalid
	}

	ticker := time.NewTicker(schedule)
	defer ticker.Stop()

	// Do first backup immediately
	if err := backuper.Backup(); err != nil {
		logger.Errorf("Initial backup failed: %v", err)
	}

	// Keep the program running and do periodic backups
	for {
		select {
		case <-ticker.C:
			if err := backuper.Backup(); err != nil {
				logger.Errorf("Scheduled backup failed: %v", err)
			}
		}
	}
}

func showCommandHelp() {
	if len(os.Args) < 3 {
		fmt.Print(helpText)
		return
	}

	switch os.Args[2] {
	case "setup":
		fmt.Println(`
Setup command:
    yorokobi setup

    Runs the interactive setup wizard to configure:
    - Backup repository location and credentials
    - Database detection and selection
    - File system paths to backup
    - Backup schedule
        `)
	case "backup":
		fmt.Println(`
Backup command:
    yorokobi backup

    Performs a one-time backup of all configured:
    - Databases (PostgreSQL, MySQL, Redis)
    - File system paths
    - Encrypts and stores in the configured repository
        `)
	case "start":
		fmt.Println(`
Start command:
    yorokobi start

    Starts the backup daemon which:
    - Runs in the background
    - Performs periodic backups based on schedule
    - Logs activity to configured location
        `)
	default:
		fmt.Printf("Unknown command: %s\nRun 'yorokobi help' for usage.\n", os.Args[2])
	}
}
