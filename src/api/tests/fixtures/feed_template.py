import pytest
import uuid

from db.feed_template import FeedTemplate, FeedTemplateParameter


@pytest.fixture(scope="function")
def unique_feed_template() -> FeedTemplate:
    """Generates unique feed template data for each test"""

    parameter = FeedTemplateParameter(
        name="param_name",
        required=True,
        type="text",
        default="default value",
        example="example value",
        title="title",
        # options={"A": "a", "B": "b", "C": "c"},
    )

    feed_template = FeedTemplate(
        name=f"Feed Template Name {uuid.uuid4()}",
        bridge_short_name="test",
        url="http://example.com",
        description="Description",
        context="by user",
        parameters=[parameter],
    )

    yield feed_template

    if feed_template.exists():
        feed_template.delete()


@pytest.fixture(scope="function")
def existing_feed_template(unique_feed_template: FeedTemplate) -> FeedTemplate:
    """Generates existing feed template data for each test"""
    unique_feed_template.create()
    yield unique_feed_template
