"""
Test cases for data serialization and JSONB handling
"""
import pytest
import uuid
from datetime import datetime
from app.utils.serialization import serialize_for_jsonb, prepare_model_data_for_db, safe_model_dump
from app.schemas.freelancer import FreelancerCreate, Specialization
from app.schemas.order import OrderCreate, OrderCondition, OrderSpecialization


class TestSerialization:
    """Test serialization utilities"""
    
    def test_serialize_basic_types(self):
        """Test serialization of basic Python types"""
        assert serialize_for_jsonb(None) is None
        assert serialize_for_jsonb("string") == "string"
        assert serialize_for_jsonb(123) == 123
        assert serialize_for_jsonb(123.45) == 123.45
        assert serialize_for_jsonb(True) is True
        assert serialize_for_jsonb(False) is False

    def test_serialize_uuid(self):
        """Test UUID serialization"""
        test_uuid = uuid.uuid4()
        result = serialize_for_jsonb(test_uuid)
        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_serialize_datetime(self):
        """Test datetime serialization"""
        test_datetime = datetime.now()
        result = serialize_for_jsonb(test_datetime)
        assert isinstance(result, str)
        assert result == test_datetime.isoformat()

    def test_serialize_enum(self):
        """Test enum serialization"""
        from app.schemas.freelancer import SkillLevel
        result = serialize_for_jsonb(SkillLevel.JUNIOR)
        assert result == "junior"

    def test_serialize_list(self):
        """Test list serialization"""
        test_list = [1, "string", uuid.uuid4()]
        result = serialize_for_jsonb(test_list)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == 1
        assert result[1] == "string"
        assert isinstance(result[2], str)

    def test_serialize_dict(self):
        """Test dictionary serialization"""
        test_dict = {
            "number": 123,
            "string": "test",
            "uuid": uuid.uuid4(),
            "nested": {"inner": "value"}
        }
        result = serialize_for_jsonb(test_dict)
        assert isinstance(result, dict)
        assert result["number"] == 123
        assert result["string"] == "test"
        assert isinstance(result["uuid"], str)
        assert result["nested"]["inner"] == "value"

    def test_serialize_pydantic_model(self):
        """Test Pydantic model serialization"""
        specialization = Specialization(
            specialization="fullstack",
            skill_level="junior"
        )
        result = serialize_for_jsonb(specialization)
        expected = {
            "specialization": "fullstack",
            "skill_level": "junior"
        }
        assert result == expected

    def test_prepare_freelancer_data(self):
        """Test preparing freelancer data for database"""
        freelancer_data = FreelancerCreate(
            iin="123456789012",
            city="Almaty",
            email="test@example.com",
            specializations_with_levels=[
                Specialization(specialization="fullstack", skill_level="junior")
            ]
        )
        
        result = prepare_model_data_for_db(freelancer_data)
        
        assert isinstance(result, dict)
        assert result["iin"] == "123456789012"
        assert result["city"] == "Almaty"
        assert result["email"] == "test@example.com"
        assert isinstance(result["specializations_with_levels"], list)
        assert len(result["specializations_with_levels"]) == 1
        assert result["specializations_with_levels"][0]["specialization"] == "fullstack"
        assert result["specializations_with_levels"][0]["skill_level"] == "junior"

    def test_prepare_order_data(self):
        """Test preparing order data with complex nested structure"""
        order_condition = OrderCondition(
            salary=5000.0,
            pay_per="month",
            required_experience=2,
            schedule_type="full-time",
            format_type="remote"
        )
        
        order_specializations = [
            OrderSpecialization(
                specialization="python",
                skill_level="middle",
                conditions=order_condition,
                requirements="Python experience required",
                vacancy_id=uuid.uuid4()
            ),
            OrderSpecialization(
                specialization="fastapi",
                skill_level="junior",
                requirements="Basic FastAPI knowledge",
                vacancy_id=uuid.uuid4()
            )
        ]
        
        order_data = OrderCreate(
            order_description="Test order",
            order_title="Test Title",
            order_specializations=order_specializations,
            name="John",
            surname="Doe",
            company_name="Test Company",
            company_position="Manager"
        )
        
        result = prepare_model_data_for_db(order_data, exclude_fields={"name", "surname"})
        
        assert isinstance(result, dict)
        assert result["order_description"] == "Test order"
        assert result["order_title"] == "Test Title"
        assert isinstance(result["order_specializations"], list)
        assert len(result["order_specializations"]) == 2
        assert result["order_specializations"][0]["specialization"] == "python"
        assert result["order_specializations"][0]["skill_level"] == "middle"
        assert result["order_specializations"][0]["conditions"]["salary"] == 5000.0
        assert result["order_specializations"][0]["requirements"] == "Python experience required"
        assert result["order_specializations"][1]["specialization"] == "fastapi"
        assert result["order_specializations"][1]["skill_level"] == "junior"
        assert result["order_specializations"][1]["requirements"] == "Basic FastAPI knowledge"
        assert "name" not in result
        assert "surname" not in result

    def test_safe_model_dump(self):
        """Test safe model dump with exclude_unset"""
        from app.schemas.freelancer import FreelancerUpdate
        
        update_data = FreelancerUpdate(
            city="New City"
        )
        
        result = safe_model_dump(update_data, exclude_unset=True)
        
        assert isinstance(result, dict)
        assert result["city"] == "New City"
        assert "iin" not in result  # Should be excluded as it's unset
        assert "email" not in result  # Should be excluded as it's unset


if __name__ == "__main__":
    pytest.main([__file__])
