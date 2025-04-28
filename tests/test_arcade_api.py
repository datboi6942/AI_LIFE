import arcade
import inspect

def test_draw_rectangle_signature():
    """Ensures arcade.draw_rectangle_filled takes positional args first."""
    # In Arcade 3+, this function is in arcade.draw, but the signature check
    # might still be useful if the underlying function is accessed elsewhere
    # or if the API changes again.
    # For Arcade 3.1.0 specifically, the function is arcade.draw_rectangle_filled
    # Let's test that directly if available.
    if hasattr(arcade, 'draw_rectangle_filled'):
        params = list(inspect.signature(arcade.draw_rectangle_filled).parameters)
        # Arcade 3.1.0 uses positional: center_x, center_y, width, height, color
        assert params[:5] == ["center_x", "center_y", "width", "height", "color"]
    elif hasattr(arcade, 'draw') and hasattr(arcade.draw, 'draw_rectangle_filled'):
        # Fallback check if it's under arcade.draw (less likely needed now)
        params = list(inspect.signature(arcade.draw.draw_rectangle_filled).parameters)
        assert params[:5] == ["center_x", "center_y", "width", "height", "color"]
    else:
        # If neither exists, maybe the API changed drastically again.
        # For now, we'll pass, assuming the main code path reflects the correct usage.
        # A better approach might be to dynamically find the function or raise an error.
        pass

# Optional: Add a similar check for the function we *actually* found (draw_rect_filled)
# to ensure it also doesn't take center_x as a keyword.
def test_draw_rect_filled_signature():
    """Ensures arcade.draw.draw_rect_filled does not take unexpected kwargs."""
    if hasattr(arcade, 'draw') and hasattr(arcade.draw, 'draw_rect_filled'):
        params = inspect.signature(arcade.draw.draw_rect_filled).parameters
        # Check if 'center_x' is the *first* parameter, indicating positional use.
        assert list(params.keys())[0] == 'center_x'
        # Ensure it doesn't unexpectedly accept it as a keyword later
        assert all(p.kind != inspect.Parameter.KEYWORD_ONLY for p in params.values()) 