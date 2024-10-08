from tests.testing_utils import build_api_request_args

from db.source import Source
from db.source_template import SourceTemplate


def test_create_source_template(unique_source_template):
    assert unique_source_template.exists() is False
    unique_source_template.create()
    assert unique_source_template.exists() is True


def test_list_all_templates(client, existing_source_template, token):
    args = build_api_request_args(
        path="/source_template/list_all",
        token=token,
    )

    response = client.get(**args)

    assert response.status_code == 200
    assert existing_source_template.name_hash in response.json()


def test_create_source_from_template(
    client, existing_source_template, existing_feed, token, unique_source
):
    args = build_api_request_args(
        path="/source_template/create",
        token=token,
        data={
            "source_template_name_hash": existing_source_template.name_hash,
            "feed_hash": existing_feed.name_hash,
            "source_name": unique_source.name,
            "parameters": {"parameter_name": "value"},
        },
    )

    response = client.post(**args)

    assert response.status_code == 200
    res_data = response.json()

    new_source = Source.read_by_key(unique_source.key)

    assert new_source.exists()
    assert new_source.name == unique_source.name

    assert res_data["source_name"] == new_source.name
    assert res_data["source_name_hash"] == new_source.name_hash
    assert (
        res_data["source_url"]
        == "http://dev-aggy-rss-bridge/?action=display&bridge=test&format=Atom&context=by+user&parameter_name=value"
    )
    assert str(new_source.url) == res_data["source_url"]
    assert res_data["source_feed"] == existing_feed.name_hash


def test_get_source_template(client, existing_source_template, token):
    args = build_api_request_args(
        path="/source_template/get",
        token=token,
        params={"name_hash": existing_source_template.name_hash},
    )

    response = client.get(**args)

    assert response.status_code == 200
    res_data = response.json()

    print("res_data: ", res_data)
    print(type(existing_source_template.json))
    assert res_data["name"] == existing_source_template.name
    assert res_data["context"] == existing_source_template.context
    assert res_data["bridge_short_name"] == existing_source_template.bridge_short_name


def test_get_nonexistent_source_template(client, token):
    args = build_api_request_args(
        path="/source_template/get",
        token=token,
        params={"name_hash": "nonexistent_source_template"},
    )

    response = client.get(**args)

    assert response.status_code == 404


def create_source_with_nonexistent_template(
    client, existing_feed, token, unique_source
):
    args = build_api_request_args(
        path="/source_template/create",
        token=token,
        data={
            "source_template_name_hash": "nonexistent_source_template",
            "feed_hash": existing_feed.name_hash,
            "source_name": unique_source.name,
            "parameters": {"parameter_name": "value"},
        },
    )

    response = client.post(**args)

    assert response.status_code == 404


def search_source_templates(
    client,
    existing_source_template,
    token,
):
    # make some dummy source templates
    for i in range(5):
        source_template = SourceTemplate(
            name=f"test_template_{i}",
            context="test",
            bridge_short_name="test",
        )
        source_template.create()

    args = build_api_request_args(
        path="/source_template/search",
        token=token,
        params={
            "query": existing_source_template.name,
            "limit": "3",
        },
    )

    response = client.get(**args)

    assert response.status_code == 200
    res_data = response.json()

    assert existing_source_template.exists() is True
    assert isinstance(res_data, list)
    assert len(res_data) == 3
    assert res_data[0]["name"] == existing_source_template.name

    # check that the next template in the response is one of the dummy templates
    assert "test_template_" in res_data[1]["name"]
