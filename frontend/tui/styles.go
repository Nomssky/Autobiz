package main

import "github.com/charmbracelet/lipgloss"

var (
	subtle    = lipgloss.AdaptiveColor{Light: "#D9DCCF", Dark: "#383838"}
	highlight = lipgloss.AdaptiveColor{Light: "#874BFD", Dark: "#7B59E0"}
	special   = lipgloss.AdaptiveColor{Light: "#43BF6D", Dark: "#73F59F"}
	warn      = lipgloss.AdaptiveColor{Light: "#E06C75", Dark: "#E06C75"}
	info      = lipgloss.AdaptiveColor{Light: "#61AFEF", Dark: "#61AFEF"}

	appStyle = lipgloss.NewStyle().
			Padding(1, 2)

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FAFAFA")).
			Background(lipgloss.Color("#7B59E0")).
			Padding(0, 1).
			MarginBottom(1)

	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#7B59E0")).
			Padding(0, 1)

	subtitleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#A0A0A0")).
			Padding(0, 1)

	tabStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, false, true, false).
			BorderForeground(highlight).
			Padding(0, 2).
			Foreground(lipgloss.Color("#A0A0A0"))

	activeTabStyle = tabStyle.
			Copy().
			BorderForeground(special).
			Foreground(lipgloss.Color("#FAFAFA")).
			Bold(true)

	tabPanelStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), true, true, true, true).
			BorderForeground(subtle).
			Padding(1, 2).
			MarginTop(-1)

	itemStyle = lipgloss.NewStyle().
			PaddingLeft(2).
			Foreground(lipgloss.Color("#E0E0E0"))

	selectedItemStyle = lipgloss.NewStyle().
				PaddingLeft(1).
				Foreground(lipgloss.Color("#7B59E0")).
				Bold(true)

	detailStyle = lipgloss.NewStyle().
			Padding(1, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(highlight)

	statusStyle = lipgloss.NewStyle().
			Padding(0, 1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#43BF6D"))

	errorStyle = lipgloss.NewStyle().
			Foreground(warn).
			Bold(true)

	successStyle = lipgloss.NewStyle().
			Foreground(special).
			Bold(true)

	helpStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#626262")).
			Padding(0, 1)

	inputStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, false, true, false).
			BorderForeground(subtle).
			Padding(0, 1)

	focusedInputStyle = inputStyle.Copy().
				BorderForeground(highlight)

	buttonStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FAFAFA")).
			Background(lipgloss.Color("#7B59E0")).
			Padding(0, 3).
			MarginTop(1).
			Bold(true)

	approveBtnStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FAFAFA")).
			Background(lipgloss.Color("#43BF6D")).
			Padding(0, 2).
			MarginRight(1).
			Bold(true)

	rejectBtnStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FAFAFA")).
			Background(lipgloss.Color("#E06C75")).
			Padding(0, 2).
			Bold(true)

	spinnerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#7B59E0"))
)
