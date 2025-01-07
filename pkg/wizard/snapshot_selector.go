package wizard

import (
	"fmt"
	"strings"

	"yorokobi-agent/pkg/backups"

	"github.com/manifoldco/promptui"
)

func SelectSnapshot(snapshots []backups.Snapshot) (*backups.Snapshot, error) {
	templates := &promptui.SelectTemplates{
		Label:    "{{ . }}",
		Active:   "\u276F {{ .Time.Format \"2006-01-02 15:04:05\" | cyan }} ({{ .Size | cyan }}) {{ index .Paths 0 | cyan }}",
		Inactive: "  {{ .Time.Format \"2006-01-02 15:04:05\" }} ({{ .Size }}) {{ index .Paths 0 }}",
		Selected: "\u276F {{ \"Snapshot selected:\" | green }} {{ .ID }}",
		Details: `
--------- Snapshot Details ----------
{{ "ID:" | faint }}	{{ .ID }}
{{ "Time:" | faint }}	{{ .Time.Format "2006-01-02 15:04:05" }}
{{ "Size:" | faint }}	{{ .Size }}
{{ "Host:" | faint }}	{{ .Hostname }}
{{ "Paths:" | faint }}	{{ range .Paths }}
	{{ . }}{{ end }}`,
	}

	prompt := promptui.Select{
		Label:     "Select snapshot to restore",
		Items:     snapshots,
		Templates: templates,
		Size:      10,
		Searcher: func(input string, index int) bool {
			snapshot := snapshots[index]
			content := fmt.Sprintf("%s %s %s",
				snapshot.Time.Format("2006-01-02 15:04:05"),
				snapshot.ID,
				strings.Join(snapshot.Paths, " "))
			return strings.Contains(strings.ToLower(content), strings.ToLower(input))
		},
	}

	i, _, err := prompt.Run()
	if err != nil {
		return nil, fmt.Errorf("snapshot selection cancelled: %v", err)
	}

	return &snapshots[i], nil
}
