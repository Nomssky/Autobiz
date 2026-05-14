package main

type appState int

const (
	stateLogin appState = iota
	stateRegister
	stateDashboard
)

type user struct {
	ID       int    `json:"id"`
	Email    string `json:"email"`
	Username string `json:"username"`
	Token    string `json:"token"`
}

type business struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Status      string `json:"status"`
	Idea        string `json:"idea"`
	CreatedAt   string `json:"created_at"`
	UpdatedAt   string `json:"updated_at"`
}

type businessDetail struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Status      string `json:"status"`
	Idea        string `json:"idea"`
	CreatedAt   string `json:"created_at"`
	UpdatedAt   string `json:"updated_at"`
	Progress    int    `json:"progress"`
	Agents      []agentStatus `json:"agents"`
}

type agentStatus struct {
	Name   string `json:"name"`
	Status string `json:"status"`
	Output string `json:"output"`
}

type approvalRequest struct {
	ID         int    `json:"id"`
	BusinessID int    `json:"business_id"`
	Title      string `json:"title"`
	AgentName  string `json:"agent_name"`
	Summary    string `json:"summary"`
	Details    string `json:"details"`
	Status     string `json:"status"`
	CreatedAt  string `json:"created_at"`
	BusinessName string `json:"business_name"`
}

type metricSnapshot struct {
	ID         int     `json:"id"`
	BusinessID int     `json:"business_id"`
	Name       string  `json:"name"`
	Value      float64 `json:"value"`
	Unit       string  `json:"unit"`
	Timestamp  string  `json:"timestamp"`
}

type tab int

const (
	tabDashboard tab = iota
	tabBusinesses
	tabApprovals
	tabMetrics
)

type page int

const (
	pageList page = iota
	pageDetail
	pageCreate
)

type errMsg struct{ err error }

func (e errMsg) Error() string { return e.err.Error() }

type successMsg struct{ message string }

type loggedInMsg struct{ user user }

type businessesLoadedMsg struct{ businesses []business }

type businessCreatedMsg struct{ business business }

type approvalsLoadedMsg struct{ approvals []approvalRequest }

type metricsLoadedMsg struct{ metrics []metricSnapshot }
