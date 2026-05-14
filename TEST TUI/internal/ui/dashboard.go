package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

type DashboardView struct {
	BizCount      int
	ApprovalCount int
	MetricCount   int
	PendingCount  int
}

func NewDashboardView() DashboardView { return DashboardView{} }

func (v DashboardView) SetCounts(biz, approvals, metrics, pending int) DashboardView {
	v.BizCount = biz
	v.ApprovalCount = approvals
	v.MetricCount = metrics
	v.PendingCount = pending
	return v
}

func (v DashboardView) Render(user *api.Client) string {
	var sb strings.Builder

	greeting := "Hey"
	if user.UserName != "" {
		greeting = "Hey, " + user.UserName
	}
	sb.WriteString(StyleTitle.Render(greeting) + "\n")
	sb.WriteString(StyleMuted.Render("Here's what's happening with your businesses.") + "\n\n")

	// Stat cards
	cards := []struct {
		label string
		value string
		style lipgloss.Style
	}{
		{"Businesses", fmt.Sprintf("%d", v.BizCount), StyleSuccess},
		{"Approvals", fmt.Sprintf("%d", v.ApprovalCount), StyleInfo},
		{"Metrics", fmt.Sprintf("%d", v.MetricCount), StyleWarn},
	}

	renderedCards := make([]string, len(cards))
	for i, c := range cards {
		inner := c.style.Bold(true).Render(c.value) + "\n" +
			StyleMuted.Render(c.label)
		renderedCards[i] = StyleStatCard.Render(inner)
	}
	sb.WriteString(lipgloss.JoinHorizontal(lipgloss.Top, renderedCards...) + "\n\n")

	// Pending warning
	if v.PendingCount > 0 {
		sb.WriteString(StyleWarn.Render(
			fmt.Sprintf("⚠  %d pending approval(s) need your attention", v.PendingCount),
		) + "\n\n")
	} else {
		sb.WriteString(StyleSuccess.Render("✓  All caught up — no pending approvals") + "\n\n")
	}

	// Quick help
	helps := []string{
		StyleHelp.Render("1-4") + " switch tabs",
		StyleHelp.Render("n") + " new business",
		StyleHelp.Render("q") + " quit",
	}
	sb.WriteString(StyleDim.Render(strings.Join(helps, "  ·  ")))

	return sb.String()
}