package main

import (
	"autobiz/internal/api"
	"autobiz/internal/ui"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
)

type screen int

const (
	screenAuth screen = iota
	screenDashboard
)

type appModel struct {
	client *api.Client
	screen screen

	auth       ui.AuthModel
	dash       ui.DashboardView
	biz        ui.BizModel
	approvals  ui.ApprovalModel
	metrics    ui.MetricModel
	settings   ui.SettingsModel
	activeTab  int

	width  int
	height int
	err    string
	quit   bool
}

func initialModel() appModel {
	c := api.New()
	return appModel{
		client:    c,
		screen:    screenAuth,
		auth:      ui.NewAuthModel(c),
		dash:      ui.NewDashboardView(),
		biz:       ui.NewBizModel(c),
		approvals: ui.NewApprovalModel(c),
		metrics:   ui.NewMetricModel(c),
		settings:  ui.NewSettingsModel(c),
	}
}

func (m appModel) Init() tea.Cmd {
	return tea.Batch(
		m.auth.Init(),
		m.biz.Init(),
		m.approvals.Init(),
		m.metrics.Init(),
	)
}

func (m appModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

	case tea.KeyMsg:
		if m.quit {
			return m, tea.Quit
		}
		switch msg.String() {
		case "ctrl+c", "q":
			if m.screen == screenDashboard {
				m.quit = true
				return m, tea.Quit
			}
		}
		if m.screen == screenDashboard {
			tabKeys := map[string]int{"1": 0, "2": 1, "3": 2, "4": 3, "5": 4}
			if t, ok := tabKeys[msg.String()]; ok {
				m.activeTab = t
				switch t {
				case 1:
					return m, m.biz.Init()
				case 2:
					return m, m.approvals.Init()
				case 3:
					return m, m.metrics.Init()
				case 4:
					return m, m.settings.Init()
				}
				return m, nil
			}
		}

	case ui.LoginSuccessMsg:
		m.screen = screenDashboard
		cmds = append(cmds,
			m.biz.Init(),
			m.approvals.Init(),
			m.metrics.Init(),
			m.settings.Init(),
		)
		return m, tea.Batch(cmds...)

	case ui.LoginErrMsg:
		return m, nil
	}

	var cmd tea.Cmd
	switch m.screen {
	case screenAuth:
		m.auth, cmd = m.auth.Update(msg)
	case screenDashboard:
		switch m.activeTab {
		case 0:
			if keyMsg, ok := msg.(tea.KeyMsg); ok && keyMsg.String() == "n" {
				m.activeTab = 1
			}
		case 1:
			m.biz, cmd = m.biz.Update(msg)
		case 2:
			m.approvals, cmd = m.approvals.Update(msg)
		case 3:
			m.metrics, cmd = m.metrics.Update(msg)
		case 4:
			m.settings, cmd = m.settings.Update(msg)
		}
	}

	return m, cmd
}

func (m appModel) View() string {
	if m.quit {
		return "\n  See you later!\n\n"
	}

	switch m.screen {
	case screenAuth:
		return m.auth.View()
	case screenDashboard:
		return m.dashboardView()
	}
	return ""
}

func (m appModel) dashboardView() string {
	tabLabels := []string{"Dashboard", "Businesses", "Approvals", "Metrics", "Settings"}

	var tabBar string
	for i, label := range tabLabels {
		if i == m.activeTab {
			tabBar += ui.StyleActiveTab.Render(fmt.Sprintf("%d:%s", i+1, label))
		} else {
			tabBar += ui.StyleInactiveTab.Render(fmt.Sprintf("%d:%s", i+1, label))
		}
	}

	header := ui.StyleTitle.Render("AutoBiz Engine") +
		ui.StyleMuted.Render("  |  "+m.client.UserEmail)

	var content string
	switch m.activeTab {
	case 0:
		d := m.dash.SetCounts(
			len(m.biz.Items()),
			len(m.approvals.Items()),
			len(m.metrics.Items()),
			m.approvals.PendingCount(),
		)
		content = d.Render(m.client)
	case 1:
		content = m.biz.View()
	case 2:
		content = m.approvals.View()
	case 3:
		content = m.metrics.View()
	case 4:
		content = m.settings.View()
	}

	return ui.StyleApp.Render(header + "\n\n" + tabBar + "\n\n" + content)
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
