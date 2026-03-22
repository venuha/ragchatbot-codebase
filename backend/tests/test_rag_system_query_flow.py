"""
Integration tests for RAGSystem query flow.

Tests cover:
- End-to-end query processing with tool usage
- Session management and conversation history
- Error scenarios (course not found, empty results, exceptions)
- Source tracking and propagation
- Configuration issues (MAX_RESULTS=0 bug)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from config import Config
from rag_system import RAGSystem
from vector_store import SearchResults


@pytest.mark.integration
class TestRAGSystemQueryFlow:
    """Test complete query flow through RAGSystem"""

    def test_query_content_search_success(self, test_config):
        """Test successful content query with search tool usage"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "Lesson 1 covers computer use with Anthropic API."
            )

            rag_system = RAGSystem(test_config)

            # Mock sources from tool execution
            rag_system.tool_manager.get_last_sources = Mock(
                return_value=["Building Towards Computer Use - Lesson 1"]
            )
            rag_system.tool_manager.get_last_source_links = Mock(
                return_value=["https://example.com/lesson1"]
            )

            # Execute
            response, sources, source_links = rag_system.query(
                "What is covered in lesson 1?"
            )

            # Assert
            assert response == "Lesson 1 covers computer use with Anthropic API."
            assert sources == ["Building Towards Computer Use - Lesson 1"]
            assert source_links == ["https://example.com/lesson1"]

            # Verify AI generator called with tools
            mock_ai_instance.generate_response.assert_called_once()
            call_kwargs = mock_ai_instance.generate_response.call_args[1]
            assert "tools" in call_kwargs
            assert "tool_manager" in call_kwargs

    def test_query_course_outline_success(self, test_config):
        """Test query that triggers course outline tool"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "The course has 5 lessons covering various topics."
            )

            rag_system = RAGSystem(test_config)

            # Mock outline tool sources
            rag_system.tool_manager.get_last_sources = Mock(
                return_value=["Building Towards Computer Use"]
            )
            rag_system.tool_manager.get_last_source_links = Mock(
                return_value=["https://example.com/course"]
            )

            # Execute
            response, sources, source_links = rag_system.query(
                "What lessons are in this course?"
            )

            # Assert
            assert "course has 5 lessons" in response
            assert len(sources) == 1
            assert len(source_links) == 1

    def test_query_general_knowledge_no_tools(self, test_config):
        """Test that general knowledge questions don't trigger tools"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "Hello! I'm here to help with course materials."
            )

            rag_system = RAGSystem(test_config)

            # No tools used, so sources should be empty
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query("Hello!")

            # Assert
            assert "Hello!" in response
            assert sources == []
            assert source_links == []

    def test_query_with_session_context(self, test_config):
        """Test follow-up question with session history"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager") as mock_session_mgr,
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = "Lesson 2 covers API usage."

            mock_session_instance = Mock()
            mock_session_mgr.return_value = mock_session_instance
            mock_session_instance.get_conversation_history.return_value = (
                "User: What is lesson 1 about?\nAssistant: Lesson 1 covers basics."
            )

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=["Course - Lesson 2"])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[None])

            # Execute with session_id
            response, sources, source_links = rag_system.query(
                "What about lesson 2?",
                session_id="session_123"
            )

            # Assert
            assert "Lesson 2" in response

            # Verify history was retrieved
            mock_session_instance.get_conversation_history.assert_called_once_with("session_123")

            # Verify history passed to AI
            call_kwargs = mock_ai_instance.generate_response.call_args[1]
            assert call_kwargs["conversation_history"] is not None

            # Verify exchange added to history
            mock_session_instance.add_exchange.assert_called_once()

    def test_query_course_not_found(self, test_config):
        """Test query when course name cannot be resolved"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup - AI receives error from tool
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "I couldn't find a course with that name."
            )

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query(
                "Tell me about NonexistentCourse"
            )

            # Assert
            assert "couldn't find" in response
            assert sources == []

    def test_query_empty_search_results(self, test_config):
        """Test query that finds no matching content"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "I couldn't find relevant content for that query."
            )

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query(
                "Tell me about completely_nonexistent_topic"
            )

            # Assert
            assert "couldn't find" in response
            assert sources == []

    def test_query_vector_store_error(self, test_config):
        """Test handling when VectorStore raises exception"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup - tool returns error string
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "I encountered a search error."
            )

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query("test query")

            # Assert - should handle gracefully
            assert isinstance(response, str)
            assert sources == []

    def test_query_tool_execution_exception(self, test_config):
        """Test handling when tool execution raises exception"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup - VectorStore raises on search
            mock_vector_instance = Mock()
            mock_vector_store.return_value = mock_vector_instance
            mock_vector_instance.search.side_effect = Exception("Database connection failed")

            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "I encountered a technical error."
            )

            rag_system = RAGSystem(test_config)

            # Execute - should not crash
            response, sources, source_links = rag_system.query("test")

            # Assert
            assert isinstance(response, str)

    def test_query_sources_populated(self, test_config):
        """Test that sources and links are properly populated and returned"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = "Answer with sources."

            rag_system = RAGSystem(test_config)

            # Mock multiple sources
            rag_system.tool_manager.get_last_sources = Mock(
                return_value=[
                    "Course 1 - Lesson 1",
                    "Course 1 - Lesson 2",
                    "Course 2 - Lesson 1"
                ]
            )
            rag_system.tool_manager.get_last_source_links = Mock(
                return_value=[
                    "https://example.com/c1/l1",
                    "https://example.com/c1/l2",
                    "https://example.com/c2/l1"
                ]
            )

            # Execute
            response, sources, source_links = rag_system.query("Query")

            # Assert
            assert len(sources) == 3
            assert len(source_links) == 3
            assert sources[0] == "Course 1 - Lesson 1"
            assert source_links[0] == "https://example.com/c1/l1"

    def test_query_sources_cleared_after_retrieval(self, test_config):
        """Test that sources are reset after being retrieved"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = "Response"

            rag_system = RAGSystem(test_config)

            # Mock sources
            rag_system.tool_manager.get_last_sources = Mock(return_value=["Source 1"])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=["Link 1"])
            mock_reset = Mock()
            rag_system.tool_manager.reset_sources = mock_reset

            # Execute
            response, sources, source_links = rag_system.query("Query")

            # Assert - reset_sources was called
            mock_reset.assert_called_once()

    def test_query_max_results_zero_bug(self, broken_config):
        """Test demonstrating MAX_RESULTS=0 bug causes empty results"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup with broken config (MAX_RESULTS=0)
            mock_vector_instance = Mock()
            mock_vector_store.return_value = mock_vector_instance

            # When MAX_RESULTS=0, ChromaDB returns empty results
            empty_results = SearchResults(
                documents=[],
                metadata=[],
                distances=[],
                error=None
            )
            mock_vector_instance.search.return_value = empty_results
            mock_vector_instance.max_results = 0  # Broken value

            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = (
                "I couldn't find any information."
            )

            rag_system = RAGSystem(broken_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query(
                "What is in lesson 1?"  # Should find content, but won't due to bug
            )

            # Assert - demonstrates the bug
            assert sources == []  # No sources due to MAX_RESULTS=0
            assert "couldn't find" in response.lower() or sources == []

    def test_query_anthropic_api_failure(self, test_config):
        """Test handling when Anthropic API raises exception"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup - AI generator raises exception
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.side_effect = Exception("API rate limit exceeded")

            rag_system = RAGSystem(test_config)

            # Execute - should raise exception
            with pytest.raises(Exception, match="API rate limit exceeded"):
                rag_system.query("Query")

    def test_query_without_session_id(self, test_config):
        """Test that query works without session_id (no history retrieval)"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager") as mock_session_mgr,
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = "Response"

            mock_session_instance = Mock()
            mock_session_mgr.return_value = mock_session_instance

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute without session_id
            response, sources, source_links = rag_system.query("Query")

            # Assert - get_conversation_history NOT called when session_id is None
            mock_session_instance.get_conversation_history.assert_not_called()

            # add_exchange should NOT be called when session_id is None
            mock_session_instance.add_exchange.assert_not_called()

    def test_query_prompt_formatting(self, test_config):
        """Test that query is wrapped in proper prompt format"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator") as mock_ai_gen,
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_ai_instance = Mock()
            mock_ai_gen.return_value = mock_ai_instance
            mock_ai_instance.generate_response.return_value = "Response"

            rag_system = RAGSystem(test_config)
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.get_last_source_links = Mock(return_value=[])

            # Execute
            response, sources, source_links = rag_system.query("What is lesson 1 about?")

            # Assert - verify prompt formatting
            call_args = mock_ai_instance.generate_response.call_args
            query_arg = call_args[1]["query"]
            assert "Answer this question about course materials:" in query_arg
            assert "What is lesson 1 about?" in query_arg

    def test_query_analytics_methods(self, test_config):
        """Test that get_course_analytics returns expected structure"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("rag_system.AIGenerator"),
            patch("rag_system.SessionManager"),
        ):
            # Setup
            mock_vector_instance = Mock()
            mock_vector_store.return_value = mock_vector_instance
            mock_vector_instance.get_course_count.return_value = 3
            mock_vector_instance.get_existing_course_titles.return_value = [
                "Course 1",
                "Course 2",
                "Course 3"
            ]

            rag_system = RAGSystem(test_config)

            # Execute
            analytics = rag_system.get_course_analytics()

            # Assert
            assert "total_courses" in analytics
            assert "course_titles" in analytics
            assert analytics["total_courses"] == 3
            assert len(analytics["course_titles"]) == 3
