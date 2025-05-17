# Memory Bank Document Orchestration Rules

## Document Types and Purposes

### 1. Project Brief (projectbrief.md)
- **Purpose**: Acts as the project's foundation document defining key objectives
- **When to Update**: At project initiation and when scope changes
- **Structure**:
  - Project Vision & Goals
  - Key Stakeholders
  - Success Metrics
  - Constraints & Limitations
  - Timeline Overview
- **Commands**:
  - `update_document projectbrief` - Update project brief details
  - `query_memory_bank "project goals"` - Find project goal information

### 2. Product Context (productContext.md)
- **Purpose**: Details product functionality, user experience, and market position
- **When to Update**: When features change or market requirements shift
- **Structure**:
  - User Personas
  - Feature List & Priorities
  - User Stories
  - Competitive Analysis
  - Product Roadmap
- **Commands**:
  - `update_document productContext` - Update product information
  - `query_memory_bank "features"` - Find feature-related information

### 3. System Patterns (systemPatterns.md)
- **Purpose**: Documents system architecture and design decisions
- **When to Update**: When architectural decisions are made or changed
- **Structure**:
  - System Architecture
  - Component Diagrams
  - Design Patterns Used
  - Integration Points
  - Data Flow
- **Commands**:
  - `update_document systemPatterns` - Update system architecture information
  - `query_memory_bank "architecture"` - Find architecture information

### 4. Tech Context (techContext.md)
- **Purpose**: Technical details, stack choices, and tooling decisions
- **When to Update**: When technology decisions are made or changed
- **Structure**:
  - Technology Stack
  - Development Environment
  - Deployment Process
  - Performance Considerations
  - Technical Debt
- **Commands**:
  - `update_document techContext` - Update technology information
  - `query_memory_bank "stack"` - Find technology stack information

### 5. Active Context (activeContext.md)
- **Purpose**: Current tasks, open questions, and active development
- **When to Update**: Daily or when switching focus areas
- **Structure**:
  - Current Sprint Goals
  - Active Tasks
  - Blockers & Challenges
  - Decisions Needed
  - Next Actions
- **Commands**:
  - `update_document activeContext` - Update current work information
  - `query_memory_bank "current tasks"` - Find information about active work

### 6. Progress (progress.md)
- **Purpose**: Progress tracking and milestone documentation
- **When to Update**: After completing tasks or reaching milestones
- **Structure**:
  - Milestones Achieved
  - Current Progress Status
  - Sprint/Cycle History
  - Learnings & Adjustments
  - Next Milestones
- **Commands**:
  - `update_document progress` - Update project progress information
  - `query_memory_bank "milestone"` - Find milestone information

## Document Workflow Processes

### Project Initialization
1. Create project brief with clear goals
2. Define product context based on brief
3. Establish initial system patterns
4. Document technology decisions
5. Set up initial active context and progress tracking

### Feature Development Cycle
1. Update active context with new feature details
2. Reference system patterns for implementation guidance
3. Document technical decisions in tech context
4. Update progress when feature is completed
5. Ensure product context reflects new capabilities

### Project Review Process
1. Review progress against project brief goals
2. Validate system patterns match implementation
3. Update product context with feedback/learnings
4. Document technical challenges in tech context
5. Set new goals in active context

## Best Practices

### Document Maintenance
- Keep documents concise and focused
- Use markdown formatting for readability
- Include diagrams where appropriate (store in resources/)
- Link between documents when referencing related content
- Update documents regularly based on the workflow process

### Collaboration Guidelines
- Review document changes with team members
- Hold regular sync meetings to update active context
- Use version control for tracking document history
- Maintain changelog entries in progress.md
- Cross-reference documents to maintain consistency

## Command Reference
- `initialize_memory_bank` - Create a new Memory Bank structure
- `update_document <docType>` - Update specific document content
- `query_memory_bank <query>` - Search across all documents
- `export_memory_bank` - Export current Memory Bank state

## Document Integration Flow
Project Brief → Product Context → System Patterns → Tech Context → Active Context → Progress

Follow this integration flow to ensure proper document orchestration and maintain project coherence.
