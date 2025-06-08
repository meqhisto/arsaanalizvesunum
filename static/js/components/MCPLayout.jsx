import React from 'react';
import styled from 'styled-components';

const MCPLayoutContainer = styled.div`
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background: var(--mcp-background);
  color: var(--mcp-text);

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const MCPMainContent = styled.main`
  padding: 2rem;
  background: var(--mcp-surface);
  border-radius: 12px;
  margin: 1rem;
  box-shadow: var(--mcp-shadow);
`;

const MCPSidebar = styled.aside`
  background: var(--mcp-surface-alt);
  padding: 1.5rem;
  border-right: 1px solid var(--mcp-border);

  @media (max-width: 768px) {
    display: none;
  }
`;

export const MCPLayout = ({ children, sidebar }) => {
  return (
    <MCPLayoutContainer>
      <MCPSidebar>{sidebar}</MCPSidebar>
      <MCPMainContent>{children}</MCPMainContent>
    </MCPLayoutContainer>
  );
};
