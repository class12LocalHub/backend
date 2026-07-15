import os
import tempfile
import unittest


TEST_DIRECTORY = tempfile.TemporaryDirectory()
os.environ["LOCALHUB_DB_PATH"] = os.path.join(
    TEST_DIRECTORY.name,
    "localhub-test.db",
)
os.environ["CORS_ORIGINS"] = (
    "http://localhost:5173,https://frontend.example.com"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.location import Location  # noqa: E402
from app.routers.categories import router as categories_router  # noqa: E402
from app.routers.chat import router as chat_router  # noqa: E402
from app.routers.dashboard import router as dashboard_router  # noqa: E402
from app.routers.items import router as items_router  # noqa: E402
from app.routers.locations import router as locations_router  # noqa: E402
from app.routers.posts import router as posts_router  # noqa: E402


class LocalHubSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app, raise_server_exceptions=False)
        with SessionLocal() as db:
            location = Location(
                source_id="126508",
                name="경복궁",
                initial_consonants="ㄱㅂㄱ",
                category="관광지",
                address="서울특별시 종로구 사직로 161",
                latitude=37.579617,
                longitude=126.977041,
            )
            db.add(location)
            db.commit()
            db.refresh(location)
            cls.sqlite_location_id = location.id

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        engine.dispose()
        TEST_DIRECTORY.cleanup()

    def test_routes_are_unique(self) -> None:
        routers = [
            posts_router,
            locations_router,
            items_router,
            dashboard_router,
            categories_router,
            chat_router,
        ]
        operations: list[tuple[str, str]] = []

        for router in routers:
            for route in router.routes:
                for method in route.methods or []:
                    operations.append((method, route.path))

        self.assertEqual(len(operations), len(set(operations)))

    def test_health_categories_dashboard_and_pagination(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        categories = self.client.get("/api/categories")
        self.assertEqual(categories.status_code, 200)
        self.assertEqual(len(categories.json()["categories"]), 7)

        dashboard = self.client.get("/api/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(
            set(dashboard.json()),
            {"region", "total_locations", "category_counts"},
        )

        invalid_page_size = self.client.get("/api/map/pois?size=0")
        self.assertEqual(invalid_page_size.status_code, 422)

        map_list = self.client.get("/api/map/pois?size=1")
        self.assertEqual(map_list.status_code, 200)
        self.assertEqual(len(map_list.json()["items"]), 1)

        map_filters = self.client.get("/api/map/filters")
        self.assertEqual(map_filters.status_code, 200)
        self.assertIn("categories", map_filters.json())

        location_list = self.client.get("/api/locations?size=1")
        self.assertEqual(location_list.status_code, 200)
        self.assertEqual(len(location_list.json()["items"]), 1)

    def test_static_suggestions_precede_dynamic_location_route(self) -> None:
        suggestions = self.client.get(
            "/api/locations/suggestions",
            params={"keyword": "ㄱㅂㄱ"},
        )
        self.assertEqual(suggestions.status_code, 200)
        item = suggestions.json()["items"][0]
        self.assertEqual(item["id"], self.sqlite_location_id)
        self.assertEqual(item["source_id"], "126508")

        json_location = self.client.get("/api/locations/2611482")
        self.assertEqual(json_location.status_code, 200)
        self.assertEqual(json_location.json()["id"], 2611482)

        map_detail = self.client.get("/api/map/pois/2611482")
        self.assertEqual(map_detail.status_code, 200)
        self.assertEqual(map_detail.json()["id"], 2611482)

    def test_post_crud_uses_sqlite_location_id(self) -> None:
        request_body = {
            "title": "경복궁 방문 후기",
            "content": "테스트 게시글입니다.",
            "password": "1234",
            "category": "관광지",
            "location_id": self.sqlite_location_id,
            "custom_tags": ["궁궐"],
            "image_url": None,
        }
        created = self.client.post("/api/posts", json=request_body)
        self.assertEqual(created.status_code, 201)
        created_post = created.json()["post"]
        post_id = created_post["id"]

        post_list = self.client.get("/api/posts")
        self.assertEqual(post_list.status_code, 200)
        self.assertEqual(post_list.json()["items"][0]["id"], post_id)

        detail = self.client.get(f"/api/posts/{post_id}")
        self.assertEqual(detail.status_code, 200)
        detail_body = detail.json()
        self.assertEqual(detail_body["location_id"], self.sqlite_location_id)
        self.assertEqual(detail_body["location"]["id"], self.sqlite_location_id)
        self.assertEqual(detail_body["location"]["source_id"], "126508")
        self.assertEqual(
            detail_body["updated_at"],
            created_post["updated_at"],
        )

        invalid_map_id = self.client.post(
            "/api/posts",
            json={**request_body, "location_id": 2611482},
        )
        self.assertEqual(invalid_map_id.status_code, 404)

        updated = self.client.put(
            f"/api/posts/{post_id}",
            json={**request_body, "title": "수정된 경복궁 방문 후기"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["post"]["title"], "수정된 경복궁 방문 후기")

        deleted = self.client.request(
            "DELETE",
            f"/api/posts/{post_id}",
            json={"password": "1234"},
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["deleted_id"], post_id)

        missing = self.client.get(f"/api/posts/{post_id}")
        self.assertEqual(missing.status_code, 404)

    def test_chat_and_location_source_ids(self) -> None:
        response = self.client.post(
            "/api/chat",
            json={
                "message": "서울 관광지를 추천해줘",
                "history": [],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["query_type"], "관광지추천")
        self.assertTrue(body["sources"])
        self.assertEqual(body["sources"][0]["type"], "location")
        self.assertGreater(body["sources"][0]["id"], 6518)

    def test_configured_production_cors_origin(self) -> None:
        response = self.client.options(
            "/api/posts",
            headers={
                "Origin": "https://frontend.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://frontend.example.com",
        )


if __name__ == "__main__":
    unittest.main()
