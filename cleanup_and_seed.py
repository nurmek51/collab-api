import asyncio
import hashlib
import uuid
from app.config.firebase import initialize_firebase
from app.datastore.firestore import get_firestore_store
from app.repositories.user import UserRepository
from app.repositories.client import ClientRepository
from app.repositories.company import CompanyRepository
from app.repositories.order import OrderRepository
from app.repositories.freelancer import FreelancerRepository
from app.repositories.order_application import OrderApplicationRepository
from app.services.order import OrderService
from app.schemas.order import OrderCreate, OrderCondition, OrderSpecialization


def generate_vacancy_id(spec: dict) -> str:
    """Generate a deterministic vacancy_id based on specialization content."""
    key_fields = {k: v for k, v in spec.items() if k in ['specialization', 'skill_level', 'conditions', 'requirements']}
    key_str = str(sorted(key_fields.items()))
    return str(uuid.UUID(hashlib.md5(key_str.encode('utf-8')).hexdigest()))


async def cleanup_database():
    """Clean up all data from the database"""
    print("Starting database cleanup...")

    # Initialize Firebase
    initialize_firebase()
    store = get_firestore_store()

    # Collections to clean up
    collections = [
        "users",
        "clients",
        "companies",
        "orders",
        "freelancers",
        "order_applications"
    ]

    for collection in collections:
        print(f"Cleaning up collection: {collection}")
        try:
            # Get all documents in the collection (no filters, no limit)
            from app.datastore.firestore import QueryOptions
            options = QueryOptions()  # Empty options to get all documents
            documents = await store.query(collection, options)
            for doc in documents:
                # Find the ID field in the document
                doc_id = None
                for possible_id in ['id', 'user_id', 'client_id', 'company_id', 'order_id', 'freelancer_id', 'application_id']:
                    if possible_id in doc:
                        doc_id = str(doc[possible_id])
                        break
                if doc_id:
                    await store.delete_document(collection, doc_id)
                    print(f"  Deleted document: {doc_id}")
            print(f"  Collection {collection} cleaned up")
        except Exception as e:
            print(f"  Error cleaning up {collection}: {e}")

    print("Database cleanup completed!")


async def create_test_data():
    """Create test data as requested"""
    print("Creating test data...")

    # Initialize Firebase
    initialize_firebase()

    # Initialize repositories
    user_repo = UserRepository()
    client_repo = ClientRepository()
    company_repo = CompanyRepository()
    order_repo = OrderRepository()
    freelancer_repo = FreelancerRepository()

    # Create client user with phone number +77777777770
    client_user = await user_repo.create_with_roles({
        "name": "Test",
        "surname": "Client",
        "phone_number": "+77777777770"
    }, ["client"])
    print(f"Created client user: {client_user.user_id} with phone: {client_user.phone_number}")

    # Create client entity
    client = await client_repo.create({
        "user_id": str(client_user.user_id)
    })
    print(f"Created client: {client.client_id}")

    # Create company
    company = await company_repo.create({
        "client_id": str(client.client_id),
        "company_name": f"Test Company {uuid.uuid4().hex[:8]}",  # Make it unique
        "company_description": "A test company for development purposes"
    })
    print(f"Created company: {company.company_id}")

    # Create 3 orders by this client
    orders = []
    order_service = OrderService()
    
    for i in range(1, 4):
        # Create OrderCreate object with proper schema
        order_condition = OrderCondition(
            salary=5000 + (i * 1000),  # Different salaries: 5000, 6000, 7000
            pay_per="month",
            required_experience=i,  # 1, 2, 3 years
            schedule_type="full-time",
            format_type="remote"
        )
        
        specializations = []
        if i <= 2:  # Only first 2 orders have specializations
            spec1 = {
                "specialization": "Python Developer",
                "skill_level": "middle" if i == 1 else "senior" if i == 2 else "junior",
                "requirements": f"Python development experience for project {i}",
            }
            spec2 = {
                "specialization": "React Developer", 
                "skill_level": "middle",
                "requirements": f"Frontend development with React for project {i}",
            }
            specializations = [
                OrderSpecialization(
                    **spec1,
                    vacancy_id=generate_vacancy_id(spec1),
                    is_occupied=False,
                    occupied_by_freelancer_id=None
                ),
                OrderSpecialization(
                    **spec2,
                    vacancy_id=generate_vacancy_id(spec2),
                    is_occupied=False,
                    occupied_by_freelancer_id=None
                )
            ]
        else:
            spec3 = {
                "specialization": "DevOps Engineer",
                "skill_level": "senior",
                "requirements": f"DevOps and infrastructure experience for project {i}",
            }
            specializations = [
                OrderSpecialization(
                    **spec3,
                    vacancy_id=generate_vacancy_id(spec3),
                    is_occupied=False,
                    occupied_by_freelancer_id=None
                )
            ]
        
        order_create_data = OrderCreate(
            order_description=f"Order {i} description - We need skilled developers for our project",
            order_title=f"Development Project {i}",
            requirements=f"Requirements for project {i}: Experience with modern technologies, good communication skills",
            order_condition=order_condition,
            order_specializations=specializations,
            # Since user and company already exist, we can pass None for these
            # The service will use existing company if it finds one with matching name
            name=None,
            surname=None,
            company_name=company.company_name,  # Use existing company name
            company_position="CEO"  # Default position
        )

        order_response = await order_service.create_order(client_user.user_id, order_create_data)
        orders.append(order_response)
        print(f"Created order {i}: {order_response.order_id} - {order_response.order_title}")

    # Create freelancer with all fields filled
    freelancer_user = await user_repo.create_with_roles({
        "name": "John",
        "surname": "Doe",
        "phone_number": "+77777777771"
    }, ["freelancer"])
    print(f"Created freelancer user: {freelancer_user.user_id}")

    freelancer = await freelancer_repo.create({
        "user_id": str(freelancer_user.user_id),
        "iin": "123456789012",
        "city": "Almaty",
        "email": "john.doe@example.com",
        "specializations_with_levels": [
            {"specialization": "Python", "level": "Senior"},
            {"specialization": "React", "level": "Middle"},
            {"specialization": "DevOps", "level": "Middle"}
        ],
        "status": "approved",
        "payment_info": {
            "bank_name": "Kaspi Bank",
            "account_number": "1234567890123456",
            "card_holder_name": "John Doe"
        },
        "social_links": {
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "telegram": "@johndoe_dev"
        },
        "portfolio_links": {
            "personal_website": "https://johndoe.dev",
            "github_portfolio": "https://github.com/johndoe/portfolio"
        },
        "avatar_url": "https://example.com/avatar.jpg",
        "bio": "Passionate full-stack developer with expertise in modern web technologies. Always eager to learn new technologies and tackle challenging projects."
    })
    print(f"Created freelancer: {freelancer.freelancer_id} with all fields filled")

    print("\nTest data creation completed!")
    print(f"Client phone: +77777777770")
    print(f"Created {len(orders)} orders")
    print(f"Freelancer created with ID: {freelancer.freelancer_id}")


async def main():
    """Main function to clean up database and create test data"""
    await cleanup_database()
    print("\n" + "="*50 + "\n")
    await create_test_data()


if __name__ == "__main__":
    asyncio.run(main())