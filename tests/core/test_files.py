import os
from unittest.mock import patch, MagicMock
from app.core.files import subfolder_check, delete_file


# Test for subfolder_check
@patch("os.path.exists")
@patch("os.makedirs")
def test_subfolder_check(mock_makedirs, mock_exists):
    # Case 1: Folder does not exist
    mock_exists.return_value = False  # Simulate that folder doesn't exist
    subfolder_path = "some/nonexistent/path"

    subfolder_check(subfolder_path)

    # Assert that makedirs was called since the folder doesn't exist
    mock_makedirs.assert_called_once_with(subfolder_path)
    mock_exists.assert_called_once_with(subfolder_path)

    # Reset mocks for the next case
    mock_makedirs.reset_mock()
    mock_exists.reset_mock()

    # Case 2: Folder already exists
    mock_exists.return_value = True  # Simulate existing folder

    subfolder_check(subfolder_path)

    # Assert that makedirs was NOT called since the folder already exists
    mock_makedirs.assert_not_called()
    mock_exists.assert_called_once_with(subfolder_path)


# Test for delete_file
@patch("os.remove")
def test_delete_file(mock_remove):
    # Case 1: File deletion is successful
    file_path = "some/file/path.txt"

    delete_file(file_path)

    # Assert os.remove was called to delete the file
    mock_remove.assert_called_once_with(file_path)

    # Reset mock for the next case
    mock_remove.reset_mock()

    # Case 2: FileNotFoundError is raised
    mock_remove.side_effect = FileNotFoundError

    delete_file(file_path)

    # Ensure we handled the FileNotFoundError (mocked by not breaking)
    mock_remove.assert_called_once_with(file_path)

    # Reset mock for the next case
    mock_remove.reset_mock()

    # Case 3: PermissionError is raised
    mock_remove.side_effect = PermissionError

    delete_file(file_path)

    # Again, ensure we handled the PermissionError
    mock_remove.assert_called_once_with(file_path)

    # Reset mock
    mock_remove.reset_mock()

    # Case 4: Generic exception is raised
    mock_remove.side_effect = Exception("Generic error")

    delete_file(file_path)

    # Ensure we handled the generic exception too
    mock_remove.assert_called_once_with(file_path)