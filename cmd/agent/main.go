package main

import (
    "fmt"
    "log"
    "os"
    "time"

    "yorokobi-agent/pkg/config"
    "yorokobi-agent/pkg/logging"
    "yorokobi-agent/pkg/backups"
    "yorokobi-agent/pkg/wizard"
)

func main() {
    // 1. Load config
    cfg, err := config.LoadConfig("config.yaml")
    if err != nil {
        log.Fatalf("failed to load config: %v", err)
    }

    // 2. Initialize logger
    logger := logging.NewLogger(&logging.Config{
        Level: cfg.Logging.Level,
    })

    // 3. Handle commands
    if len(os.Args) > 1 {
        switch os.Args[1] {
        case "setup":
            runSetup(cfg, logger)
        case "backup":
            runBackup(cfg, logger)
        case "daemon":
            runDaemon(cfg, logger)
        default:
            fmt.Printf("Unknown command: %s\n", os.Args[1])
            fmt.Println("Available commands: setup, backup, daemon")
            os.Exit(1)
        }
        return
    }

    // If no command provided, run as daemon
    runDaemon(cfg, logger)
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