"""
Comprehensive tests for CourseSearchTool.execute() method.

Tests cover:
- Successful search execution with various filters
- Error handling and propagation
- Source tracking and link retrieval
- Tool definition structure validation
"""

import pytest
from unittest.mock import Mock, patch

from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


@pytest.mark.unit
class TestCourseSearchToolExecute:
    """Test CourseSearchTool.execute() method comprehensively"""

    def test_execute_basic_search_success(self, mock_vector_store, sample_search_results):
        """Test successful search without any filters"""
        # Setup
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("What is computer use?")

        # Assert
        assert "[Building Towards Computer Use with Anthropic - Lesson 1]" in result
        assert "Welcome to Building Toward Computer Use" in result

        # Verify vector store called correctly
        mock_vector_store.search.assert_called_once_with(
            query="What is computer use?",
            course_name=None,
            lesson_number=None,
        )

    def test_execute_with_course_filter_success(self, mock_vector_store, sample_search_results):
        """Test search with course_name filter"""
        # Setup
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="What is covered?",
            course_name="Anthropic Course"
        )

        # Assert
        assert "Building Towards Computer Use with Anthropic" in result
        mock_vector_store.search.assert_called_once_with(
            query="What is covered?",
            course_name="Anthropic Course",
            lesson_number=None,
        )

    def test_execute_with_lesson_filter_success(self, mock_vector_store, sample_search_results):
        """Test search with lesson_number filter"""
        # Setup
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="lesson content",
            lesson_number=1
        )

        # Assert
        assert "Lesson 1" in result
        mock_vector_store.search.assert_called_once_with(
            query="lesson content",
            course_name=None,
            lesson_number=1,
        )

    def test_execute_with_both_filters_success(self, mock_vector_store, sample_search_results):
        """Test search with both course and lesson filters"""
        # Setup
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="specific content",
            course_name="Test Course",
            lesson_number=2
        )

        # Assert
        assert isinstance(result, str)
        mock_vector_store.search.assert_called_once_with(
            query="specific content",
            course_name="Test Course",
            lesson_number=2,
        )

    def test_execute_empty_results_handling(self, mock_vector_store):
        """Test handling of empty search results"""
        # Setup - empty results
        empty_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = empty_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("nonexistent content")

        # Assert
        assert result == "No relevant content found."
        assert tool.last_sources == []
        assert tool.last_source_links == []

    def test_execute_empty_results_with_course_filter(self, mock_vector_store):
        """Test empty results message includes filter info"""
        # Setup
        empty_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = empty_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="nonexistent",
            course_name="Test Course"
        )

        # Assert
        assert "No relevant content found in course 'Test Course'" in result

    def test_execute_empty_results_with_lesson_filter(self, mock_vector_store):
        """Test empty results message includes lesson filter info"""
        # Setup
        empty_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = empty_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="nonexistent",
            lesson_number=5
        )

        # Assert
        assert "No relevant content found in lesson 5" in result

    def test_execute_empty_results_with_both_filters(self, mock_vector_store):
        """Test empty results message includes both filters"""
        # Setup
        empty_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = empty_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="nonexistent",
            course_name="Test Course",
            lesson_number=3
        )

        # Assert
        assert "in course 'Test Course'" in result
        assert "in lesson 3" in result

    def test_execute_vector_store_error_handling(self, mock_vector_store):
        """Test that SearchResults.error is properly propagated"""
        # Setup - results with error
        error_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="Search error: Database connection failed"
        )
        mock_vector_store.search.return_value = error_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("test query")

        # Assert
        assert result == "Search error: Database connection failed"

    def test_execute_course_not_found_error(self, mock_vector_store):
        """Test handling when course name cannot be resolved"""
        # Setup - course not found error
        error_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="No course found matching 'Invalid Course'"
        )
        mock_vector_store.search.return_value = error_results
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute(
            query="test",
            course_name="Invalid Course"
        )

        # Assert
        assert "No course found matching 'Invalid Course'" in result

    def test_execute_search_exception_handling(self, mock_vector_store):
        """Test handling when VectorStore.search raises exception"""
        # Setup - search raises exception
        mock_vector_store.search.side_effect = Exception("Unexpected error")
        tool = CourseSearchTool(mock_vector_store)

        # Execute & Assert - should raise exception (not caught by execute)
        with pytest.raises(Exception, match="Unexpected error"):
            tool.execute("test query")

    def test_source_tracking_single_document(self, mock_vector_store):
        """Test that sources and links are tracked correctly for single result"""
        # Setup
        single_result = SearchResults(
            documents=["This is lesson 1 content"],
            metadata=[{
                "course_title": "Test Course",
                "lesson_number": 1,
                "chunk_index": 0
            }],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = single_result
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("test query")

        # Assert
        assert "[Test Course - Lesson 1]" in result
        assert tool.last_sources == ["Test Course - Lesson 1"]
        assert tool.last_source_links == ["https://example.com/lesson1"]

        # Verify get_lesson_link was called
        mock_vector_store.get_lesson_link.assert_called_once_with("Test Course", 1)

    def test_source_tracking_multiple_documents(self, mock_vector_store):
        """Test source tracking with multiple documents"""
        # Setup
        multiple_results = SearchResults(
            documents=[
                "Content from lesson 1",
                "Content from lesson 2",
                "More content from lesson 1"
            ],
            metadata=[
                {"course_title": "Test Course", "lesson_number": 1, "chunk_index": 0},
                {"course_title": "Test Course", "lesson_number": 2, "chunk_index": 1},
                {"course_title": "Test Course", "lesson_number": 1, "chunk_index": 2}
            ],
            distances=[0.1, 0.2, 0.3]
        )
        mock_vector_store.search.return_value = multiple_results
        mock_vector_store.get_lesson_link.side_effect = [
            "https://example.com/lesson1",
            "https://example.com/lesson2",
            "https://example.com/lesson1"
        ]
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("test query")

        # Assert
        assert len(tool.last_sources) == 3
        assert tool.last_sources[0] == "Test Course - Lesson 1"
        assert tool.last_sources[1] == "Test Course - Lesson 2"
        assert tool.last_sources[2] == "Test Course - Lesson 1"

        assert len(tool.last_source_links) == 3
        assert tool.last_source_links[0] == "https://example.com/lesson1"
        assert tool.last_source_links[1] == "https://example.com/lesson2"
        assert tool.last_source_links[2] == "https://example.com/lesson1"

    def test_source_tracking_no_lesson_number(self, mock_vector_store):
        """Test source tracking when lesson_number is None"""
        # Setup
        result_no_lesson = SearchResults(
            documents=["General course content"],
            metadata=[{
                "course_title": "Test Course",
                "lesson_number": None,
                "chunk_index": 0
            }],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = result_no_lesson
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = tool.execute("test query")

        # Assert
        assert "[Test Course]" in result  # No lesson number in header
        assert tool.last_sources == ["Test Course"]
        assert tool.last_source_links == [None]

        # Verify get_lesson_link was NOT called
        mock_vector_store.get_lesson_link.assert_not_called()

    def test_source_tracking_cleared_via_tool_manager(self, mock_vector_store, sample_search_results):
        """Test that sources can be cleared through ToolManager"""
        # Setup
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

        tool_manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        tool_manager.register_tool(tool)

        # Execute tool
        tool_manager.execute_tool("search_course_content", query="test")

        # Verify sources exist
        assert len(tool.last_sources) > 0
        assert len(tool.last_source_links) > 0

        # Reset sources
        tool_manager.reset_sources()

        # Assert sources cleared
        assert tool.last_sources == []
        assert tool.last_source_links == []

    def test_get_tool_definition_structure(self, mock_vector_store):
        """Test that tool definition has correct structure"""
        # Setup
        tool = CourseSearchTool(mock_vector_store)

        # Execute
        definition = tool.get_tool_definition()

        # Assert structure
        assert "name" in definition
        assert definition["name"] == "search_course_content"

        assert "description" in definition
        assert isinstance(definition["description"], str)

        assert "input_schema" in definition
        schema = definition["input_schema"]
        assert schema["type"] == "object"

        assert "properties" in schema
        properties = schema["properties"]
        assert "query" in properties
        assert "course_name" in properties
        assert "lesson_number" in properties

        assert "required" in schema
        assert schema["required"] == ["query"]

    def test_tool_definition_parameter_descriptions(self, mock_vector_store):
        """Test that tool parameters have proper descriptions"""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        definition = tool.get_tool_definition()
        properties = definition["input_schema"]["properties"]

        # Assert
        assert "description" in properties["query"]
        assert "description" in properties["course_name"]
        assert "description" in properties["lesson_number"]

        # Verify types
        assert properties["query"]["type"] == "string"
        assert properties["course_name"]["type"] == "string"
        assert properties["lesson_number"]["type"] == "integer"
