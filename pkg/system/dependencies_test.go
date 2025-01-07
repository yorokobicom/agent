package system

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

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

func TestCheckAndInstall(t *testing.T) {
	origExecCommand := execCommand
	defer func() { execCommand = origExecCommand }()

	tests := []struct {
		name        string
		dependency  Dependency
		mockCmd     func(name string, args ...string) *exec.Cmd
		expectError bool
	}{
		{
			name: "already installed",
			dependency: Dependency{
				Name:        "test-dep",
				BrewPackage: "test-dep",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				if name == "which" {
					return exec.Command("true") // Simulate command exists
				}
				return exec.Command("true") // All other commands succeed
			},
			expectError: false,
		},
		{
			name: "needs installation",
			dependency: Dependency{
				Name:        "missing-dep",
				BrewPackage: "missing-dep",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				if name == "which" {
					return exec.Command("false") // Simulate command doesn't exist
				}
				if name == "brew" {
					return exec.Command("true") // Simulate successful installation
				}
				return exec.Command("true")
			},
			expectError: false,
		},
		{
			name: "installation fails",
			dependency: Dependency{
				Name:        "failing-dep",
				BrewPackage: "failing-dep",
			},
			mockCmd: func(name string, args ...string) *exec.Cmd {
				return exec.Command("false") // All commands fail
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			logger := logging.NewMockLogger()
			checker := NewSystemChecker(logger)

			execCommand = tt.mockCmd
			err := checker.checkAndInstallDependency(tt.dependency)
			if (err != nil) != tt.expectError {
				t.Errorf("checkAndInstallDependency() error = %v, expectError %v", err, tt.expectError)
			}

			logs := logger.GetLogs()
			if len(logs) == 0 {
				t.Error("no logs were recorded")
			}
		})
	}
}
