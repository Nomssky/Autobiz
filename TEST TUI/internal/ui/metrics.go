package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type MetricModel struct {
	client *api.Client
	items  []api.Metric
	errMsg string
}

func NewMetricModel(client *api.Client) MetricModel {
	return MetricModel{client: client}
}

func (m MetricModel) Items() []api.Metric { return m.items }

type MetricListMsg struct{ Items []api.Metric }
type MetricErrMsg struct{ Err string }

func (m MetricModel) fetchCmd() tea.Cmd {
	return func() tea.Msg {
		items, err := m.client.ListMetrics("")
		if err != nil {
			return MetricErrMsg{Err: err.Error()}
		}
		return MetricListMsg{Items: items}
	}
}

func (m MetricModel) Init() tea.Cmd { return m.fetchCmd() }

func (m MetricModel) Update(msg tea.Msg) (MetricModel, tea.Cmd) {
	switch msg := msg.(type) {
	case MetricListMsg:
		m.items = msg.Items

	case MetricErrMsg:
		m.errMsg = msg.Err

	case tea.KeyMsg:
		m.errMsg = ""
		switch msg.String() {
		case "r":
			return m, m.fetchCmd()
		}
	}
	return m, nil
}

func (m MetricModel) View() string {
	var sb strings.Builder

	sb.WriteString(StyleTitle.Render("Metrics") + "\n\n")

	if len(m.items) == 0 {
		sb.WriteString(StyleMuted.Render("  No metrics yet.") + "\n")
		sb.WriteString("\n" + StyleDim.Render("r refresh"))
		return sb.String()
	}

	for _, mt := range m.items {
		role := StyleInfo.Render(mt.RecordedByRole)
		sb.WriteString(fmt.Sprintf("  %s\n", role))
		sb.WriteString(fmt.Sprintf("    Revenue:    $%.2f\n", mt.DailyRevenue))
		sb.WriteString(fmt.Sprintf("    Users:      %d\n", mt.UsersCount))
		sb.WriteString(fmt.Sprintf("    Churn Rate: %.1f%%\n", mt.ChurnRate*100))
		shortDate := mt.CreatedAt
		if len(shortDate) > 10 {
			shortDate = shortDate[:10]
		}
		sb.WriteString(fmt.Sprintf("    %s\n\n", StyleMuted.Render(shortDate)))
	}

	if m.errMsg != "" {
		sb.WriteString(StyleError.Render("✗ "+m.errMsg) + "\n")
	}

	sb.WriteString(StyleDim.Render("r refresh"))
	return sb.String()
}
