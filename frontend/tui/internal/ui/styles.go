package ui

import "github.com/charmbracelet/lipgloss"

// Palette
var (
	colPurple  = lipgloss.Color("#7B59E0")
	colGreen   = lipgloss.Color("#73F59F")
	colRed     = lipgloss.Color("#E06C75")
	colBlue    = lipgloss.Color("#61AFEF")
	colMuted   = lipgloss.Color("#666666")
	colDim     = lipgloss.Color("#444444")
	colWhite   = lipgloss.Color("#DDDDDD")
	colYellow  = lipgloss.Color("#E5C07B")
)

// Base styles
var (
	StyleTitle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colPurple)

	StyleSubtitle = lipgloss.NewStyle().
			Foreground(colMuted).
			Italic(true)

	StyleHighlight = lipgloss.NewStyle().
			Foreground(colPurple).
			Bold(true)

	StyleSuccess = lipgloss.NewStyle().
			Foreground(colGreen)

	StyleError = lipgloss.NewStyle().
			Foreground(colRed)

	StyleInfo = lipgloss.NewStyle().
			Foreground(colBlue)

	StyleWarn = lipgloss.NewStyle().
			Foreground(colYellow)

	StyleMuted = lipgloss.NewStyle().
			Foreground(colMuted)

	StyleDim = lipgloss.NewStyle().
			Foreground(colDim)

	StyleSelected = lipgloss.NewStyle().
			Foreground(colPurple).
			Bold(true)

	StyleNormal = lipgloss.NewStyle().
			Foreground(colWhite)

	// Tab bar
	StyleActiveTab = lipgloss.NewStyle().
			Foreground(colPurple).
			Bold(true).
			Underline(true).
			Padding(0, 2)

	StyleInactiveTab = lipgloss.NewStyle().
				Foreground(colMuted).
				Padding(0, 2)

	// Input field
	StyleInputLabel = lipgloss.NewStyle().
			Foreground(colBlue)

	StyleInputActive = lipgloss.NewStyle().
				Foreground(colWhite).
				BorderStyle(lipgloss.NormalBorder()).
				BorderBottom(true).
				BorderForeground(colPurple).
				Width(36)

	StyleInputInactive = lipgloss.NewStyle().
				Foreground(colMuted).
				BorderStyle(lipgloss.NormalBorder()).
				BorderBottom(true).
				BorderForeground(colDim).
				Width(36)

	// Stat card
	StyleStatCard = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colDim).
			Padding(0, 2).
			Width(14)

	StyleStatValue = lipgloss.NewStyle().
			Foreground(colGreen).
			Bold(true)

	// Help bar
	StyleHelp = lipgloss.NewStyle().
			Foreground(colDim)

	// App frame
	StyleApp = lipgloss.NewStyle().
			Padding(1, 3)

	// Urgency badges
	StyleUrgencyHigh   = lipgloss.NewStyle().Foreground(colRed).Bold(true)
	StyleUrgencyNormal = lipgloss.NewStyle().Foreground(colMuted)

	// Status badges
	StyleStatusBuilding  = lipgloss.NewStyle().Foreground(colYellow)
	StyleStatusOperating = lipgloss.NewStyle().Foreground(colGreen)
	StyleStatusArchived  = lipgloss.NewStyle().Foreground(colMuted)
)

func StatusStyle(s string) lipgloss.Style {
	switch s {
	case "building":
		return StyleStatusBuilding
	case "operating":
		return StyleStatusOperating
	case "archived":
		return StyleStatusArchived
	default:
		return StyleMuted
	}
}

func UrgencyStyle(u string) lipgloss.Style {
	if u == "high" || u == "HIGH" {
		return StyleUrgencyHigh
	}
	return StyleUrgencyNormal
}