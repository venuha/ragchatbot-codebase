"""
Comprehensive tests for AIGenerator tool calling functionality.

Tests cover:
- Direct responses without tool use
- Single and multiple tool calls
- Multi-round tool calling (up to 2 rounds)
- Error handling and conversation flow
- Tool execution failures
"""

import pytest
from unittest.mock import Mock, patch

from ai_generator import AIGenerator


@pytest.mark.unit
class TestAIGeneratorToolCalling:
    """Test AIGenerator.generate_response() with tool calling"""

    def test_generate_response_no_tool_use(self):
        """Test direct response without any tool calls"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock response without tool use
            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock()]
            mock_response.content[0].text = "This is a general knowledge answer."

            mock_client.messages.create.return_value = mock_response

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            response = generator.generate_response("What is 2+2?")

            # Assert
            assert response == "This is a general knowledge answer."
            assert mock_client.messages.create.call_count == 1

            # Verify no tools were passed
            call_args = mock_client.messages.create.call_args[1]
            assert "tools" not in call_args or call_args.get("tools") is None

    def test_generate_response_single_tool_call(self, mock_tool_manager):
        """Test response generation with single tool call"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock initial response with tool use
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [Mock()]
            initial_response.content[0].type = "tool_use"
            initial_response.content[0].name = "search_course_content"
            initial_response.content[0].id = "tool_123"
            initial_response.content[0].input = {"query": "lesson 1 content"}

            # Mock final response after tool execution
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Based on the search results, lesson 1 covers computer use."

            # Setup side_effect for two calls
            mock_client.messages.create.side_effect = [initial_response, final_response]

            # Setup tool manager
            mock_tool_manager.execute_tool.return_value = "Search results: Lesson 1 content..."

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "What is in lesson 1?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            assert response == "Based on the search results, lesson 1 covers computer use."
            assert mock_client.messages.create.call_count == 2

            # Verify tool was executed
            mock_tool_manager.execute_tool.assert_called_once_with(
                "search_course_content",
                query="lesson 1 content"
            )

    def test_generate_response_multiple_tools_same_round(self, mock_tool_manager):
        """Test response when multiple tools are called in one round"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Create two tool use blocks
            tool1 = Mock()
            tool1.type = "tool_use"
            tool1.name = "search_course_content"
            tool1.id = "tool_123"
            tool1.input = {"query": "first query"}

            tool2 = Mock()
            tool2.type = "tool_use"
            tool2.name = "get_course_outline"
            tool2.id = "tool_456"
            tool2.input = {"course_name": "Test Course"}

            # Mock initial response with multiple tools
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [tool1, tool2]

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Here's what I found from both searches."

            mock_client.messages.create.side_effect = [initial_response, final_response]

            # Setup tool manager to return different results
            mock_tool_manager.execute_tool.side_effect = [
                "Search result 1",
                "Outline result"
            ]

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Tell me about the course",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            assert response == "Here's what I found from both searches."
            assert mock_tool_manager.execute_tool.call_count == 2

            # Verify both tools were called
            mock_tool_manager.execute_tool.assert_any_call(
                "search_course_content",
                query="first query"
            )
            mock_tool_manager.execute_tool.assert_any_call(
                "get_course_outline",
                course_name="Test Course"
            )

    def test_generate_response_two_sequential_rounds(self, mock_tool_manager):
        """Test tool calling across 2 sequential rounds"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Round 1: Tool use
            round1_response = Mock()
            round1_response.stop_reason = "tool_use"
            round1_response.content = [Mock()]
            round1_response.content[0].type = "tool_use"
            round1_response.content[0].name = "search_course_content"
            round1_response.content[0].id = "tool_1"
            round1_response.content[0].input = {"query": "initial query"}

            # Round 2: Another tool use
            round2_response = Mock()
            round2_response.stop_reason = "tool_use"
            round2_response.content = [Mock()]
            round2_response.content[0].type = "tool_use"
            round2_response.content[0].name = "get_course_outline"
            round2_response.content[0].id = "tool_2"
            round2_response.content[0].input = {"course_name": "Course Name"}

            # Final response after max rounds
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Final answer after 2 tool rounds."

            mock_client.messages.create.side_effect = [
                round1_response,
                round2_response,
                final_response
            ]

            mock_tool_manager.execute_tool.side_effect = [
                "Result from search",
                "Result from outline"
            ]

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Complex query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            assert response == "Final answer after 2 tool rounds."
            assert mock_client.messages.create.call_count == 3  # 2 tool rounds + 1 final
            assert mock_tool_manager.execute_tool.call_count == 2

    def test_generate_response_tool_execution_failure(self, mock_tool_manager):
        """Test handling when tool execution raises exception"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool use response
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [Mock()]
            initial_response.content[0].type = "tool_use"
            initial_response.content[0].name = "search_course_content"
            initial_response.content[0].id = "tool_123"
            initial_response.content[0].input = {"query": "test"}

            # Mock final response after error
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "I encountered an error searching."

            mock_client.messages.create.side_effect = [initial_response, final_response]

            # Tool execution raises exception
            mock_tool_manager.execute_tool.side_effect = Exception("Database error")

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            assert response == "I encountered an error searching."
            assert mock_client.messages.create.call_count == 2

            # Verify error was passed to API
            second_call_args = mock_client.messages.create.call_args_list[1][1]
            messages = second_call_args["messages"]

            # Find the tool_result message
            tool_result_msg = messages[-1]
            assert tool_result_msg["role"] == "user"
            assert tool_result_msg["content"][0]["type"] == "tool_result"
            assert "Error: Tool execution failed" in tool_result_msg["content"][0]["content"]
            assert "Database error" in tool_result_msg["content"][0]["content"]

    def test_generate_response_tool_returns_error_string(self, mock_tool_manager):
        """Test when tool returns error message string (not exception)"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool use response
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [Mock()]
            initial_response.content[0].type = "tool_use"
            initial_response.content[0].name = "search_course_content"
            initial_response.content[0].id = "tool_123"
            initial_response.content[0].input = {"query": "test", "course_name": "Invalid"}

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "I couldn't find that course."

            mock_client.messages.create.side_effect = [initial_response, final_response]

            # Tool returns error string (not exception)
            mock_tool_manager.execute_tool.return_value = "No course found matching 'Invalid'"

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert - should continue normally
            assert response == "I couldn't find that course."
            assert mock_client.messages.create.call_count == 2

    def test_generate_response_empty_search_results(self, mock_tool_manager):
        """Test when tool returns 'No relevant content found' message"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool use
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [Mock()]
            initial_response.content[0].type = "tool_use"
            initial_response.content[0].name = "search_course_content"
            initial_response.content[0].id = "tool_123"
            initial_response.content[0].input = {"query": "nonexistent"}

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "I couldn't find relevant content for that query."

            mock_client.messages.create.side_effect = [initial_response, final_response]

            # Tool returns empty results message
            mock_tool_manager.execute_tool.return_value = "No relevant content found."

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            assert response == "I couldn't find relevant content for that query."

    def test_handle_tool_execution_conversation_structure(self, mock_tool_manager):
        """Test that conversation messages are structured correctly"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock tool use response
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [Mock()]
            initial_response.content[0].type = "tool_use"
            initial_response.content[0].name = "search_course_content"
            initial_response.content[0].id = "tool_123"
            initial_response.content[0].input = {"query": "test"}

            # Mock final response
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Final answer"

            mock_client.messages.create.side_effect = [initial_response, final_response]
            mock_tool_manager.execute_tool.return_value = "Tool result"

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "What's in lesson 1?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert - verify conversation structure in second API call
            assert mock_client.messages.create.call_count == 2

            second_call_args = mock_client.messages.create.call_args_list[1][1]
            messages = second_call_args["messages"]

            # Should have 3 messages: user, assistant (tool use), user (tool result)
            assert len(messages) == 3

            # Message 1: User query
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "What's in lesson 1?"

            # Message 2: Assistant with tool use
            assert messages[1]["role"] == "assistant"
            assert messages[1]["content"] == initial_response.content

            # Message 3: User with tool results
            assert messages[2]["role"] == "user"
            assert isinstance(messages[2]["content"], list)
            assert messages[2]["content"][0]["type"] == "tool_result"
            assert messages[2]["content"][0]["tool_use_id"] == "tool_123"
            assert messages[2]["content"][0]["content"] == "Tool result"

    def test_handle_tool_execution_multiple_tool_results(self, mock_tool_manager):
        """Test that multiple tool results are added as single user message"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Create two tool use blocks
            tool1 = Mock()
            tool1.type = "tool_use"
            tool1.name = "search_course_content"
            tool1.id = "tool_1"
            tool1.input = {"query": "query1"}

            tool2 = Mock()
            tool2.type = "tool_use"
            tool2.name = "get_course_outline"
            tool2.id = "tool_2"
            tool2.input = {"course_name": "course"}

            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            initial_response.content = [tool1, tool2]

            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Combined answer"

            mock_client.messages.create.side_effect = [initial_response, final_response]
            mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert - verify tool results structure
            second_call_args = mock_client.messages.create.call_args_list[1][1]
            messages = second_call_args["messages"]

            # Last message should contain both tool results
            tool_results_msg = messages[-1]
            assert tool_results_msg["role"] == "user"
            assert len(tool_results_msg["content"]) == 2

            # Verify both tool results present
            assert tool_results_msg["content"][0]["tool_use_id"] == "tool_1"
            assert tool_results_msg["content"][0]["content"] == "Result 1"
            assert tool_results_msg["content"][1]["tool_use_id"] == "tool_2"
            assert tool_results_msg["content"][1]["content"] == "Result 2"

    def test_handle_tool_execution_stops_on_exception(self, mock_tool_manager):
        """Test that should_continue=False when tool raises exception"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Round 1: Tool use that fails
            round1_response = Mock()
            round1_response.stop_reason = "tool_use"
            round1_response.content = [Mock()]
            round1_response.content[0].type = "tool_use"
            round1_response.content[0].name = "search_course_content"
            round1_response.content[0].id = "tool_1"
            round1_response.content[0].input = {"query": "test"}

            # Final response (should be called after error)
            final_response = Mock()
            final_response.stop_reason = "end_turn"
            final_response.content = [Mock()]
            final_response.content[0].text = "Error response"

            mock_client.messages.create.side_effect = [round1_response, final_response]
            mock_tool_manager.execute_tool.side_effect = Exception("Tool error")

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert - should stop after first round (only 2 API calls, not 3)
            assert mock_client.messages.create.call_count == 2
            assert mock_tool_manager.execute_tool.call_count == 1

    def test_system_prompt_included(self):
        """Test that system prompt is included in API call"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Response"

            mock_client.messages.create.return_value = mock_response

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            response = generator.generate_response("Query")

            # Assert - verify system prompt in call
            call_args = mock_client.messages.create.call_args[1]
            assert "system" in call_args
            assert "You are an AI assistant specialized in course materials" in call_args["system"]

    def test_system_prompt_with_conversation_history(self):
        """Test system prompt includes conversation history"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Response"

            mock_client.messages.create.return_value = mock_response

            # Execute with history
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            history = "User: Previous question\nAssistant: Previous answer"
            response = generator.generate_response("Follow-up query", conversation_history=history)

            # Assert
            call_args = mock_client.messages.create.call_args[1]
            assert "Previous conversation:" in call_args["system"]
            assert "Previous question" in call_args["system"]
            assert "Previous answer" in call_args["system"]

    def test_final_call_without_tools_after_max_rounds(self, mock_tool_manager):
        """Test that final call after max rounds has no tools"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            # Setup
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Two rounds of tool use
            round1 = Mock()
            round1.stop_reason = "tool_use"
            round1.content = [Mock()]
            round1.content[0].type = "tool_use"
            round1.content[0].name = "search_course_content"
            round1.content[0].id = "tool_1"
            round1.content[0].input = {"query": "q1"}

            round2 = Mock()
            round2.stop_reason = "tool_use"
            round2.content = [Mock()]
            round2.content[0].type = "tool_use"
            round2.content[0].name = "search_course_content"
            round2.content[0].id = "tool_2"
            round2.content[0].input = {"query": "q2"}

            final = Mock()
            final.stop_reason = "end_turn"
            final.content = [Mock()]
            final.content[0].text = "Final answer"

            mock_client.messages.create.side_effect = [round1, round2, final]
            mock_tool_manager.execute_tool.return_value = "Result"

            # Execute
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()
            response = generator.generate_response(
                "Query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert - third call should have no tools
            assert mock_client.messages.create.call_count == 3
            third_call_args = mock_client.messages.create.call_args_list[2][1]
            assert "tools" not in third_call_args  # No tools in final call
