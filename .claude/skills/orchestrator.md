---
name: orchestrator
description: Multi-phase workflow orchestration pattern for main agents. Enables structured planning, delegation to sub-agents, parallel execution, and result aggregation.
---

# Orchestrator Skill

You are operating with orchestration capabilities. Follow this 4-phase workflow pattern to break down complex tasks and delegate to specialized sub-agents.

## Phase 1: Planning

Before starting any work, analyze the task and create a structured plan:

<planning_instructions>
1. **Understand the Task**: Read and comprehend the full scope of what's being requested
2. **Identify Work Items**: Break the task into discrete, actionable items
3. **Assess Dependencies**: Determine which items depend on others
4. **Map to Sub-Agents**: For each work item, identify which sub-agent is best suited
5. **Identify Parallelization**: Mark items that can run concurrently (no dependencies between them)
</planning_instructions>

<plan_output_format>
Output your plan as structured XML:

```xml
<orchestration_plan>
  <task_summary>Brief description of the overall task</task_summary>

  <work_items>
    <item id="1" parallel_group="A">
      <description>What needs to be done</description>
      <sub_agent>sub-agent-name</sub_agent>
      <dependencies>none</dependencies>
      <inputs>What this sub-agent needs</inputs>
      <expected_output>What this sub-agent will produce</expected_output>
    </item>

    <item id="2" parallel_group="A">
      <description>Another independent task</description>
      <sub_agent>another-sub-agent</sub_agent>
      <dependencies>none</dependencies>
      <inputs>...</inputs>
      <expected_output>...</expected_output>
    </item>

    <item id="3" parallel_group="B">
      <description>Task that depends on items 1 and 2</description>
      <sub_agent>yet-another-sub-agent</sub_agent>
      <dependencies>1, 2</dependencies>
      <inputs>Outputs from items 1 and 2</inputs>
      <expected_output>...</expected_output>
    </item>
  </work_items>

  <execution_order>
    <parallel_group name="A" items="1, 2"/>
    <parallel_group name="B" items="3" after="A"/>
  </execution_order>
</orchestration_plan>
```
</plan_output_format>

## Phase 2: Delegation

Execute your plan by invoking sub-agents:

<delegation_rules>
1. **Parallel Execution**: Invoke all sub-agents in the same parallel_group simultaneously using multiple Task tool calls in a single message
2. **Sequential Groups**: Wait for a parallel group to complete before starting the next group
3. **Context Passing**: Pass relevant outputs from completed items as inputs to dependent items
4. **Clear Instructions**: Give each sub-agent specific, actionable instructions based on the work item
</delegation_rules>

<delegation_format>
When invoking sub-agents, use this pattern:

```
Task(subagent_type="sub-agent-name", prompt="
<task>
[Specific task description from work item]
</task>

<context>
[Any relevant context or outputs from previous items]
</context>

<expected_deliverables>
[What this sub-agent should produce]
</expected_deliverables>
")
```
</delegation_format>

## Phase 3: Execution Monitoring

As sub-agents complete their work:

<monitoring_instructions>
1. **Collect Results**: Gather outputs from each sub-agent
2. **Validate Completeness**: Ensure each sub-agent delivered expected outputs
3. **Handle Failures**: If a sub-agent fails, assess whether to retry, use fallback, or escalate
4. **Track Progress**: Update your plan status as items complete
</monitoring_instructions>

## Phase 4: Aggregation

After all sub-agents complete, synthesize results:

<aggregation_instructions>
1. **Combine Outputs**: Merge artifacts and deliverables from all sub-agents
2. **Resolve Conflicts**: If sub-agents produced conflicting outputs, reconcile them
3. **Quality Check**: Review combined output for consistency and completeness
4. **Summarize**: Provide a cohesive summary of what was accomplished
5. **Identify Gaps**: Note any remaining work or follow-up items
</aggregation_instructions>

<final_output_format>
```xml
<orchestration_result>
  <summary>Overall summary of completed work</summary>

  <completed_items>
    <item id="1" sub_agent="sub-agent-name" status="success">
      <output_summary>What was produced</output_summary>
      <artifacts>
        <artifact path="path/to/file" action="created"/>
      </artifacts>
    </item>
    <!-- More items... -->
  </completed_items>

  <combined_artifacts>
    <artifact path="path/to/file1" source="item-1"/>
    <artifact path="path/to/file2" source="item-2"/>
  </combined_artifacts>

  <warnings>
    - Any issues or concerns discovered
  </warnings>

  <next_steps>
    - Recommended follow-up actions
  </next_steps>
</orchestration_result>
```
</final_output_format>

## Parallelization Guidelines

<parallel_rules>
**CAN run in parallel:**
- Independent analysis tasks (e.g., requirements + risk assessment)
- Non-overlapping file generation (e.g., frontend components + backend models)
- Multiple test generators targeting different layers

**MUST run sequentially:**
- Tasks where output feeds into another task's input
- File modifications to the same files
- Tasks with explicit dependencies
</parallel_rules>

## Error Handling

<error_handling>
If a sub-agent fails or produces incomplete results:

1. **Assess Impact**: Determine if dependent items can proceed
2. **Retry Option**: Consider retrying with clarified instructions
3. **Fallback**: If sub-agent unavailable, attempt the work directly
4. **Escalate**: If critical failure, report to user with details
</error_handling>
