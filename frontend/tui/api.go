package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const apiBaseURL = "http://localhost:8000"

type apiClient struct {
	baseURL    string
	token      string
	httpClient *http.Client
}

func newAPIClient() *apiClient {
	return &apiClient{
		baseURL:    apiBaseURL,
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

func (c *apiClient) setToken(token string) {
	c.token = token
}

func (c *apiClient) doRequest(method, path string, body any, target any) error {
	url := c.baseURL + path
	var reqBody io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("marshal request: %w", err)
		}
		reqBody = bytes.NewReader(b)
	}

	req, err := http.NewRequest(method, url, reqBody)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		var errResp struct {
			Detail string `json:"detail"`
		}
		if json.Unmarshal(respBody, &errResp) == nil && errResp.Detail != "" {
			return fmt.Errorf("%s", errResp.Detail)
		}
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(respBody))
	}

	if target != nil {
		if err := json.Unmarshal(respBody, target); err != nil {
			return fmt.Errorf("parse response: %w", err)
		}
	}
	return nil
}

func (c *apiClient) login(email, password string) (user, error) {
	var u user
	body := map[string]string{
		"email":    email,
		"password": password,
	}
	// Try both possible endpoint patterns
	err := c.doRequest("POST", "/api/v1/auth/login", body, &u)
	if err != nil {
		// Fallback: try alternative login format
		altBody := map[string]string{
			"username": email,
			"password": password,
		}
		var altResp struct {
			AccessToken string `json:"access_token"`
			TokenType   string `json:"token_type"`
			User        user   `json:"user"`
		}
		if altErr := c.doRequest("POST", "/api/v1/auth/login", altBody, &altResp); altErr == nil {
			u = altResp.User
			u.Token = altResp.AccessToken
			return u, nil
		}
		var directResp struct {
			AccessToken string `json:"access_token"`
			TokenType   string `json:"token_type"`
			Email       string `json:"email"`
			UserID      int    `json:"user_id"`
		}
		if directErr := c.doRequest("POST", "/api/v1/auth/login", body, &directResp); directErr == nil {
			u.Token = directResp.AccessToken
			u.Email = directResp.Email
			u.ID = directResp.UserID
			return u, nil
		}
		return u, err
	}
	return u, nil
}

func (c *apiClient) register(email, username, password string) (user, error) {
	var u user
	body := map[string]string{
		"email":    email,
		"username": username,
		"password": password,
	}
	err := c.doRequest("POST", "/api/v1/auth/register", body, &u)
	if err != nil {
		// Try response that returns user directly
		var resp struct {
			User  user   `json:"user"`
			Token string `json:"token"`
		}
		if altErr := c.doRequest("POST", "/api/v1/auth/register", body, &resp); altErr == nil {
			u = resp.User
			u.Token = resp.Token
			return u, nil
		}
		return u, err
	}
	return u, nil
}

func (c *apiClient) listBusinesses() ([]business, error) {
	var businesses []business
	err := c.doRequest("GET", "/api/v1/businesses/", nil, &businesses)
	if err != nil {
		return nil, err
	}
	return businesses, nil
}

func (c *apiClient) createBusiness(idea string) (business, error) {
	var b business
	body := map[string]string{"idea": idea}
	err := c.doRequest("POST", "/api/v1/businesses/create", body, &b)
	if err != nil {
		return b, err
	}
	return b, nil
}

func (c *apiClient) getBusiness(id int) (businessDetail, error) {
	var b businessDetail
	err := c.doRequest("GET", fmt.Sprintf("/api/v1/businesses/%d", id), nil, &b)
	if err != nil {
		return b, err
	}
	return b, nil
}

func (c *apiClient) listPendingApprovals() ([]approvalRequest, error) {
	var approvals []approvalRequest
	err := c.doRequest("GET", "/api/v1/approvals/pending", nil, &approvals)
	if err != nil {
		// Try list endpoint
		err2 := c.doRequest("GET", "/api/v1/approvals/", nil, &approvals)
		if err2 != nil {
			return nil, err
		}
	}
	// Filter pending
	var pending []approvalRequest
	for _, a := range approvals {
		if a.Status == "" || a.Status == "pending" {
			pending = append(pending, a)
		}
	}
	return pending, nil
}

func (c *apiClient) decideApproval(id int, approved bool, reason string) error {
	body := map[string]any{
		"approved": approved,
		"reason":   reason,
	}
	return c.doRequest("POST", fmt.Sprintf("/api/v1/approvals/%d/decide", id), body, nil)
}

func (c *apiClient) listMetrics() ([]metricSnapshot, error) {
	var metrics []metricSnapshot
	err := c.doRequest("GET", "/api/v1/metrics/", nil, &metrics)
	if err != nil {
		return nil, err
	}
	return metrics, nil
}
