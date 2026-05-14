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
	url := c.baseURL + "/api/v1" + path
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
	body := map[string]string{"email": email, "password": password}
	err := c.doRequest("POST", "/auth/login", body, &u)
	return u, err
}

func (c *apiClient) register(email, name, password string) (user, error) {
	var u user
	body := map[string]string{"email": email, "name": name, "password": password}
	err := c.doRequest("POST", "/auth/register", body, &u)
	return u, err
}

func (c *apiClient) listBusinesses() ([]business, error) {
	var businesses []business
	err := c.doRequest("GET", "/businesses/", nil, &businesses)
	return businesses, err
}

func (c *apiClient) createBusiness(idea string) (business, error) {
	var b business
	body := map[string]string{"idea": idea}
	err := c.doRequest("POST", "/businesses/create", body, &b)
	return b, err
}

func (c *apiClient) listPendingApprovals() ([]approvalRequest, error) {
	var approvals []approvalRequest
	err := c.doRequest("GET", "/approvals/pending", nil, &approvals)
	return approvals, err
}

func (c *apiClient) decideApproval(id, ceoID string, approve bool, comments string) error {
	decision := "reject"
	if approve {
		decision = "approve"
	}
	body := map[string]any{
		"decision": decision,
		"ceo_id":   ceoID,
		"comments": comments,
	}
	return c.doRequest("POST", fmt.Sprintf("/approvals/%s/decide", id), body, nil)
}

func (c *apiClient) listMetrics() ([]metricSnapshot, error) {
	var metrics []metricSnapshot
	err := c.doRequest("GET", "/metrics/", nil, &metrics)
	return metrics, err
}
