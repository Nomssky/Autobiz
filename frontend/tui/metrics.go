package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
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

func (m model) metricsView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Metrics"))
	b.WriteString("\n\n")

	if m.dash.metrics.loading {
		b.WriteString(spinnerStyle.Render("Loading metrics..."))
		return b.String()
	}

	if len(m.dash.metrics.metrics) == 0 {
		b.WriteString(subtitleStyle.Render("No metrics available yet."))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("r: refresh • q: quit"))
		return b.String()
	}

	metricsByBusiness := make(map[int][]metricSnapshot)
	for _, m := range m.dash.metrics.metrics {
		metricsByBusiness[m.BusinessID] = append(metricsByBusiness[m.BusinessID], m)
	}

	for bizID, ms := range metricsByBusiness {
		bizName := fmt.Sprintf("Business #%d", bizID)
		for _, biz := range m.dash.businesses.businesses {
			if biz.ID == bizID {
				bizName = biz.Name
				break
			}
		}

		b.WriteString(subtitleStyle.Render(bizName))
		b.WriteString("\n")

		for _, metric := range ms {
			valColor := special
			if metric.Value < 0 {
				valColor = warn
			}

			card := lipgloss.NewStyle().
				Width(25).
				Border(lipgloss.RoundedBorder()).
				BorderForeground(subtle).
				Padding(0, 1).
				MarginRight(1).
				MarginBottom(1).
				Render(
					lipgloss.JoinVertical(lipgloss.Center,
						metric.Name,
						lipgloss.NewStyle().Bold(true).Foreground(valColor).Render(
							fmt.Sprintf("%.1f %s", metric.Value, metric.Unit),
						),
					),
				)

			b.WriteString(card)
		}
		b.WriteString("\n")
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("r: refresh • q: quit"))

	return b.String()
}
