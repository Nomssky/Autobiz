package main

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type model struct {
	state    appState
	auth     authModel
	dash     dashboardModel
	width    int
	height   int
	api      *apiClient
	user     user
	err      string
	quitting bool
}

type dashboardModel struct {
	activeTab   tab
	businesses  businessListModel
	approvals   approvalListModel
	metrics     metricsModel
	loading     bool
	err         string
}

type businessListModel struct {
	page        page
	businesses  []business
	selected    int
	loading     bool
	err         string
	ideaInput   string
	creating    bool
	detailSpin  spinner.Model
}

type approvalListModel struct {
	approvals   []approvalRequest
	selected    int
	loading     bool
	err         string
	showDetails bool
}

type metricsModel struct {
	metrics     []metricSnapshot
	loading     bool
	err         string
}

func initialModel() model {
	api := newAPIClient()
	a := newAuthModel(api)
	s := spinner.New()
	s.Style = spinnerStyle
	s.Spinner = spinner.Dot

	return model{
		state: stateLogin,
		auth:  a,
		api:   api,
		dash: dashboardModel{
			activeTab: tabDashboard,
			businesses: businessListModel{
				page:       pageList,
				detailSpin: s,
			},
		},
	}
}

func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.auth.Init(),
		spinner.Tick,
	)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case tea.KeyMsg:
		if m.quitting {
			return m, tea.Quit
		}
		switch msg.String() {
		case "ctrl+c", "q":
			m.quitting = true
			return m, tea.Quit
		}

		if m.state == stateLogin {
			return m.handleAuthKey(msg)
		}
		return m.handleDashKey(msg)

	case loggedInMsg:
		m.user = msg.user
		m.state = stateDashboard
		m.api.setToken(msg.user.AccessToken)
		cmds = append(cmds, m.loadDashboardData())

	case errMsg:
		if m.state == stateLogin || m.state == stateRegister {
			m.auth.err = msg.Error()
		} else {
			m.err = msg.Error()
		}

	case businessesLoadedMsg:
		m.dash.businesses.businesses = msg.businesses
		m.dash.businesses.loading = false

	case businessCreatedMsg:
		m.dash.businesses.businesses = append([]business{msg.business}, m.dash.businesses.businesses...)
		m.dash.businesses.creating = false
		m.dash.businesses.ideaInput = ""
		m.dash.businesses.page = pageList

	case approvalsLoadedMsg:
		m.dash.approvals.approvals = msg.approvals
		m.dash.approvals.loading = false

	case metricsLoadedMsg:
		m.dash.metrics.metrics = msg.metrics
		m.dash.metrics.loading = false

	case successMsg:
		m.err = ""
		return m, m.loadDashboardData()

	default:
		if m.state == stateLogin || m.state == stateRegister {
			var cmd tea.Cmd
			m.auth, cmd = m.auth.Update(msg)
			cmds = append(cmds, cmd)
		} else {
			cmd := m.updateDashboard(msg)
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	return m, tea.Batch(cmds...)
}

func (m model) handleAuthKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	m.auth, cmd = m.auth.Update(msg)
	return m, cmd
}

func (m model) handleDashKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg.String() {
	case "1":
		m.dash.activeTab = tabDashboard
	case "2":
		m.dash.activeTab = tabBusinesses
	case "3":
		m.dash.activeTab = tabApprovals
	case "4":
		m.dash.activeTab = tabMetrics
	case "left":
		if m.dash.activeTab > 0 {
			m.dash.activeTab--
		}
	case "right":
		if m.dash.activeTab < tabMetrics {
			m.dash.activeTab++
		}
	default:
		cmd = m.updateDashboard(msg)
	}

	return m, cmd
}

func (m *model) updateDashboard(msg tea.Msg) tea.Cmd {
	switch m.dash.activeTab {
	case tabBusinesses:
		return m.updateBusinesses(msg)
	case tabApprovals:
		return m.updateApprovals(msg)
	case tabMetrics:
		return m.updateMetrics(msg)
	default:
		return m.updateDashboardHome(msg)
	}
}

func (m *model) updateDashboardHome(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "n":
			m.dash.activeTab = tabBusinesses
			m.dash.businesses.page = pageCreate
		}
	}
	return nil
}

func (m model) loadDashboardData() tea.Cmd {
	return tea.Batch(
		m.loadBusinesses(),
		m.loadApprovals(),
		m.loadMetrics(),
	)
}

func (m model) loadBusinesses() tea.Cmd {
	return func() tea.Msg {
		businesses, err := m.api.listBusinesses()
		if err != nil {
			return errMsg{err}
		}
		return businessesLoadedMsg{businesses}
	}
}

func (m model) loadApprovals() tea.Cmd {
	return func() tea.Msg {
		approvals, err := m.api.listPendingApprovals()
		if err != nil {
			return errMsg{err}
		}
		return approvalsLoadedMsg{approvals}
	}
}

func (m model) loadMetrics() tea.Cmd {
	return func() tea.Msg {
		metrics, err := m.api.listMetrics()
		if err != nil {
			return errMsg{err}
		}
		return metricsLoadedMsg{metrics}
	}
}

func (m model) View() string {
	if m.quitting {
		return "\n  See you later!\n\n"
	}

	if m.state == stateLogin || m.state == stateRegister {
		return m.auth.View()
	}

	return m.dashboardView()
}

func (m model) dashboardView() string {
	var b strings.Builder

	b.WriteString(m.headerView())
	b.WriteString("\n")
	b.WriteString(m.tabView())
	b.WriteString("\n")

	content := m.contentView()
	b.WriteString(tabPanelStyle.Width(m.width - 6).Render(content))

	if m.err != "" {
		b.WriteString("\n")
		b.WriteString(errorStyle.Render("Error: " + m.err))
	}

	return appStyle.Render(b.String())
}

func (m model) headerView() string {
	return headerStyle.Width(m.width - 4).Render(" AutoBiz Engine " + subtitleStyle.Render("| "+m.user.Email))
}

func (m model) tabView() string {
	tabs := []struct {
		label string
		tab   tab
	}{
		{"1: Dashboard", tabDashboard},
		{"2: Businesses", tabBusinesses},
		{"3: Approvals", tabApprovals},
		{"4: Metrics", tabMetrics},
	}

	var rendered []string
	for _, t := range tabs {
		if m.dash.activeTab == t.tab {
			rendered = append(rendered, activeTabStyle.Render(t.label))
		} else {
			rendered = append(rendered, tabStyle.Render(t.label))
		}
	}

	return lipgloss.JoinHorizontal(lipgloss.Top, rendered...)
}

func (m model) contentView() string {
	switch m.dash.activeTab {
	case tabDashboard:
		return m.dashboardContentView()
	case tabBusinesses:
		return m.businessesView()
	case tabApprovals:
		return m.approvalsView()
	case tabMetrics:
		return m.metricsView()
	}
	return ""
}

func (m model) dashboardContentView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Welcome to AutoBiz Engine"))
	b.WriteString("\n\n")

	businessCount := len(m.dash.businesses.businesses)
	approvalCount := len(m.dash.approvals.approvals)
	metricCount := len(m.dash.metrics.metrics)

	b.WriteString(lipgloss.JoinHorizontal(lipgloss.Top,
		m.statCard("Businesses", fmt.Sprintf("%d", businessCount), special),
		m.statCard("Pending Approvals", fmt.Sprintf("%d", approvalCount), warn),
		m.statCard("Metrics", fmt.Sprintf("%d", metricCount), info),
	))

	b.WriteString("\n\n")

	if approvalCount > 0 {
		b.WriteString(warnStyle.Render(fmt.Sprintf("⚠ %d pending approval(s) — switch to Approvals tab", approvalCount)))
		b.WriteString("\n\n")
	}

	b.WriteString(helpStyle.Render("Press 1-4 to switch tabs • n: create business • q: quit"))

	return b.String()
}

func (m model) statCard(label, value string, color lipgloss.AdaptiveColor) string {
	style := lipgloss.NewStyle().
		Width(20).
		Height(5).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(color).
		Align(lipgloss.Center).
		MarginRight(2)

	return style.Render(
		lipgloss.JoinVertical(lipgloss.Center,
			lipgloss.NewStyle().Bold(true).Foreground(color).Render(value),
			label,
		),
	)
}
