"""
Test module for Direktor.
"""
import os
import sys

# Add the parent directory to sys.path to import direktor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_import():
    """Test that we can import the direktor package."""
    try:
        import direktor
        assert hasattr(direktor, 'generate_video')
        assert hasattr(direktor, 'optimize_content')
        print("Import test passed!")
    except Exception as e:
        print(f"Import test failed: {e}")
        raise

if __name__ == "__main__":
    test_import()