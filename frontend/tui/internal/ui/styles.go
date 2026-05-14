package ui

import "github.com/charmbracelet/lipgloss"

// ── Color Palette ──
var (
	colPrimary = lipgloss.Color("#7C3AED")
	colSuccess = lipgloss.Color("#10B981")
	colError   = lipgloss.Color("#EF4444")
	colWarn    = lipgloss.Color("#F59E0B")
	colInfo    = lipgloss.Color("#3B82F6")
	colWhite   = lipgloss.Color("#F8FAFC")
	colMuted   = lipgloss.Color("#94A3B8")
	colDim     = lipgloss.Color("#475569")
	colBg      = lipgloss.Color("#1E293B")
	colBgDark  = lipgloss.Color("#0F172A")
	colBorder  = lipgloss.Color("#334155")
	colSelBg   = lipgloss.Color("#1E1B4B")
)

// ── Text Styles ──
var (
	StyleTitle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colWhite).
			Background(colPrimary).
			Padding(0, 2)

	StyleSectionHeader = lipgloss.NewStyle().
				Bold(true).
				Foreground(colPrimary).
				Padding(0, 1)

	StyleHighlight = lipgloss.NewStyle().
			Foreground(colPrimary).
			Bold(true)

	StyleSuccess = lipgloss.NewStyle().
			Foreground(colSuccess)

	StyleError = lipgloss.NewStyle().
			Foreground(colError)

	StyleInfo = lipgloss.NewStyle().
			Foreground(colInfo)

	StyleWarn = lipgloss.NewStyle().
			Foreground(colWarn)

	StyleMuted = lipgloss.NewStyle().
			Foreground(colMuted)

	StyleDim = lipgloss.NewStyle().
			Foreground(colDim)

	StyleSelected = lipgloss.NewStyle().
			Foreground(colPrimary).
			Bold(true)

	StyleNormal = lipgloss.NewStyle().
			Foreground(colWhite)
)

// ── Tab Bar ──
var (
	StyleActiveTab = lipgloss.NewStyle().
			Foreground(colWhite).
			Background(colPrimary).
			Padding(0, 2).
			Bold(true)

	StyleInactiveTab = lipgloss.NewStyle().
				Foreground(colMuted).
				Padding(0, 2)
)

// ── Panel / Card ──
var (
	StylePanel = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colBorder).
			Padding(1, 2).
			Width(50)

	StyleStatCard = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colBorder).
			Padding(0, 2).
			Width(16)

	StyleApp = lipgloss.NewStyle().
			Padding(1, 2).
			Background(colBgDark)
)

// ── Status Badges ──
var (
	StyleStatusBuilding  = lipgloss.NewStyle().Foreground(colWarn).Bold(true)
	StyleStatusOperating = lipgloss.NewStyle().Foreground(colSuccess).Bold(true)
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

// ── Help Bar ──
var StyleHelp = lipgloss.NewStyle().Foreground(colDim)

// ── Input Fields ──
var (
	StyleInputLabel = lipgloss.NewStyle().Foreground(colInfo).Bold(true)
	StyleInputValue = lipgloss.NewStyle().Foreground(colWhite)
	StyleCursor     = lipgloss.NewStyle().Foreground(colPrimary).Bold(true)
)

// ── Approval Urgency ──
var (
	StyleUrgencyHigh   = lipgloss.NewStyle().Foreground(colError).Bold(true)
	StyleUrgencyNormal = lipgloss.NewStyle().Foreground(colMuted)
)

func UrgencyStyle(u string) lipgloss.Style {
	if u == "high" || u == "HIGH" {
		return StyleUrgencyHigh
	}
	return StyleUrgencyNormal
}

// ── Background colors for status dots ──
func StatusDot(s string) string {
	switch s {
	case "ok", "connected", "configured":
		return StyleSuccess.Render("●")
	case "error", "missing_api_key":
		return StyleError.Render("●")
	default:
		return StyleDim.Render("○")
	}
}
