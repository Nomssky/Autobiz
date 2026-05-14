package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

func (m *model) updateMetrics(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			m.dash.metrics.loading = true
			return m.loadMetrics()
		}
	}
	return nil
}

func (m *model) metricsView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Metrics"))
	b.WriteString("\n\n")

	if m.dash.metrics.loading {
		b.WriteString(infoStyle.Render("Loading..."))
		return b.String()
	}

	if len(m.dash.metrics.metrics) == 0 {
		b.WriteString(dimStyle.Render("No metrics data yet."))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("r: refresh • q: quit"))
		return b.String()
	}

	for _, mt := range m.dash.metrics.metrics {
		b.WriteString(fmt.Sprintf("  %s\n", labelStyle.Render(mt.RecordedByRole)))
		b.WriteString(fmt.Sprintf("    Revenue:    $%.2f\n", mt.DailyRevenue))
		b.WriteString(fmt.Sprintf("    Users:      %d\n", mt.UsersCount))
		b.WriteString(fmt.Sprintf("    Churn Rate: %.1f%%\n", mt.ChurnRate*100))
		b.WriteString(fmt.Sprintf("    %s\n\n", dimStyle.Render(mt.CreatedAt)))
	}

	b.WriteString(helpStyle.Render("r: refresh • q: quit"))
	return b.String()
}
