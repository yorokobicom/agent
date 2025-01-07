package wizard

import (
	"github.com/manifoldco/promptui"
)

func PromptString(label string) string {
	prompt := promptui.Prompt{
		Label: label,
	}

	result, err := prompt.Run()
	if err != nil {
		return ""
	}

	return result
}

func PromptYesNo(label string) bool {
	prompt := promptui.Prompt{
		Label:     label,
		IsConfirm: true,
	}

	result, err := prompt.Run()
	if err != nil {
		return false
	}

	return result == "y" || result == "Y"
}
