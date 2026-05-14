package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

func (m *model) updateBusinesses(msg tea.Msg) tea.Cmd {
	switch m.dash.businesses.page {
	case pageList:
		return m.updateBusinessList(msg)
	case pageCreate:
		return m.updateBusinessCreate(msg)
	case pageDetail:
		return m.updateBusinessDetail(msg)
	}
	return nil
}

func (m *model) updateBusinessList(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.dash.businesses.selected > 0 {
				m.dash.businesses.selected--
			}
		case "down", "j":
			if m.dash.businesses.selected < len(m.dash.businesses.businesses)-1 {
				m.dash.businesses.selected++
			}
		case "enter":
			if len(m.dash.businesses.businesses) > 0 {
				m.dash.businesses.page = pageDetail
			}
		case "n":
			m.dash.businesses.page = pageCreate
			m.dash.businesses.ideaInput = ""
		case "r":
			m.dash.businesses.loading = true
			return m.loadBusinesses()
		}
	}
	return nil
}

func (m *model) updateBusinessCreate(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			if m.dash.businesses.ideaInput != "" {
				m.dash.businesses.creating = true
				return m.createBusiness()
			}
		case "backspace":
			if len(m.dash.businesses.ideaInput) > 0 {
				m.dash.businesses.ideaInput = m.dash.businesses.ideaInput[:len(m.dash.businesses.ideaInput)-1]
			}
		case "esc":
			m.dash.businesses.page = pageList
		default:
			if len(msg.String()) == 1 {
				m.dash.businesses.ideaInput += msg.String()
			}
		}
	}
	return nil
}

func (m *model) updateBusinessDetail(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q", "backspace":
			m.dash.businesses.page = pageList
		}
	}
	return nil
}

func (m *model) createBusiness() tea.Cmd {
	return func() tea.Msg {
		b, err := m.api.createBusiness(m.dash.businesses.ideaInput)
		if err != nil {
			return errMsg{err}
		}
		return businessCreatedMsg{business: b}
	}
}

func (m *model) businessesView() string {
	switch m.dash.businesses.page {
	case pageCreate:
		return m.createBusinessView()
	case pageDetail:
		return m.businessDetailView()
	default:
		return m.businessListView()
	}
}

func (m *model) businessListView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Businesses"))
	b.WriteString("\n\n")

	if m.dash.businesses.loading {
		b.WriteString(infoStyle.Render("Loading..."))
		return b.String()
	}

	if len(m.dash.businesses.businesses) == 0 {
		b.WriteString(dimStyle.Render("No businesses yet. Press 'n' to create one."))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("n: new • r: refresh • q: quit"))
		return b.String()
	}

	for i, biz := range m.dash.businesses.businesses {
		prefix := "  "
		if i == m.dash.businesses.selected {
			prefix = "▸ "
		}
		line := fmt.Sprintf("%s%s  %s", prefix, biz.Name, dimStyle.Render(biz.Status))
		if i == m.dash.businesses.selected {
			b.WriteString(selectedStyle.Render(line))
		} else {
			b.WriteString(line)
		}
		b.WriteString("\n")
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("↑↓: navigate • enter: detail • n: new • r: refresh • q: quit"))
	return b.String()
}

func (m *model) createBusinessView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("New Business"))
	b.WriteString("\n\n")
	b.WriteString(inputStyle.Render("Describe your business idea:"))
	b.WriteString("\n")
	b.WriteString(valueStyle.Render(m.dash.businesses.ideaInput + cursor()))
	b.WriteString("\n\n")

	if m.dash.businesses.creating {
		b.WriteString(infoStyle.Render("Creating..."))
	} else {
		b.WriteString(helpStyle.Render("Enter: create • Esc: back"))
	}

	return b.String()
}

func (m *model) businessDetailView() string {
	if len(m.dash.businesses.businesses) == 0 {
		return ""
	}
	biz := m.dash.businesses.businesses[m.dash.businesses.selected]

	var b strings.Builder
	b.WriteString(titleStyle.Render(biz.Name))
	b.WriteString("\n\n")

	info := []struct{ label, value string }{
		{"ID", biz.ID},
		{"Status", biz.Status},
		{"Phase", biz.CurrentPhase},
		{"Created", biz.CreatedAt},
	}
	for _, item := range info {
		b.WriteString(fmt.Sprintf("%s: %s\n", labelStyle.Render(item.label), valueStyle.Render(item.value[:min(len(item.value), 36)])))
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("Esc: back"))
	return b.String()
}
