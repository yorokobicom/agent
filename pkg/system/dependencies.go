package system

import (
	"fmt"
	"os/exec"

	"yorokobi-agent/pkg/logging"
)

var execCommand = exec.Command

type Dependency struct {
	Name         string
	BrewPackage  string
	AptPackage   string
	YumPackage   string
	InstallNotes string
}

var Dependencies = []Dependency{
	{
		Name:         "restic",
		BrewPackage:  "restic",
		AptPackage:   "restic",
		YumPackage:   "restic",
		InstallNotes: "Visit https://restic.net/ for manual installation instructions",
	},
	{
		Name:         "pg_dump",
		BrewPackage:  "postgresql",
		AptPackage:   "postgresql-client",
		YumPackage:   "postgresql",
		InstallNotes: "PostgreSQL client tools are required for database backups",
	},
}

type SystemChecker struct {
	logger logging.Logger
}

func NewSystemChecker(logger logging.Logger) *SystemChecker {
	return &SystemChecker{logger: logger}
}

func (s *SystemChecker) CheckAndInstall() error {
	s.logger.Info("Checking system dependencies...")

	for _, dep := range Dependencies {
		if err := s.checkAndInstallDependency(dep); err != nil {
			return fmt.Errorf("failed to setup %s: %v", dep.Name, err)
		}
	}

	return nil
}

func (s *SystemChecker) checkAndInstallDependency(dep Dependency) error {
	// Check if already installed
	cmd := execCommand("which", dep.Name)
	if err := cmd.Run(); err == nil {
		s.logger.Info(fmt.Sprintf("%s is already installed", dep.Name))
		return nil
	}

	s.logger.Info(fmt.Sprintf("Installing %s...", dep.Name))

	// Try to install with brew first
	if dep.BrewPackage != "" {
		cmd = execCommand("brew", "install", dep.BrewPackage)
		out, err := cmd.CombinedOutput()
		if err == nil {
			s.logger.Info(fmt.Sprintf("Successfully installed %s", dep.Name))
			return nil
		}
		// If brew fails, continue to next package manager
		s.logger.Info(fmt.Sprintf("Brew install failed: %s", string(out)))
	}

	// Try apt-get
	if dep.AptPackage != "" {
		cmd = execCommand("apt-get", "install", "-y", dep.AptPackage)
		out, err := cmd.CombinedOutput()
		if err == nil {
			s.logger.Info(fmt.Sprintf("Successfully installed %s", dep.Name))
			return nil
		}
		s.logger.Info(fmt.Sprintf("Apt install failed: %s", string(out)))
	}

	// Try yum
	if dep.YumPackage != "" {
		cmd = execCommand("yum", "install", "-y", dep.YumPackage)
		out, err := cmd.CombinedOutput()
		if err == nil {
			s.logger.Info(fmt.Sprintf("Successfully installed %s", dep.Name))
			return nil
		}
		s.logger.Info(fmt.Sprintf("Yum install failed: %s", string(out)))
	}

	if dep.InstallNotes != "" {
		s.logger.Info(fmt.Sprintf("Manual installation instructions: %s", dep.InstallNotes))
	}

	return fmt.Errorf("failed to install %s with any package manager", dep.Name)
}
