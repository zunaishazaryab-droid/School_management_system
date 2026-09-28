from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.transport.models import Vehicle, Route, RouteStop, StudentTransportAllocation
from apps.library.models import BookCategory, Book, BookIssue
from apps.inventory.models import ItemCategory, Supplier, InventoryItem, StockTransaction
from apps.students.models import Student
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Seed demonstration data for Sprint 7 (Transport, Library, Inventory)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding Sprint 7 Demo Data..."))
        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        # 1. Transport Vehicles & Routes
        v1, _ = Vehicle.objects.get_or_create(
            vehicle_number='LEA-2024',
            defaults={
                'model_name': 'Toyota Coaster 30-Seater',
                'driver_name': 'Muhammad Ramzan',
                'driver_phone': '0300-1122334',
                'seating_capacity': 30,
                'status': Vehicle.Status.ACTIVE,
            }
        )
        v2, _ = Vehicle.objects.get_or_create(
            vehicle_number='LES-8841',
            defaults={
                'model_name': 'Toyota HiAce Grand Cabin',
                'driver_name': 'Tariq Mehmood',
                'driver_phone': '0321-9988776',
                'seating_capacity': 15,
                'status': Vehicle.Status.ACTIVE,
            }
        )

        r1, _ = Route.objects.get_or_create(
            title='Route 1: Gulberg - Model Town - Campus',
            defaults={
                'start_point': 'Main Market Gulberg',
                'end_point': 'Main Campus Gate A',
                'monthly_fare': Decimal('3500.00'),
                'is_active': True,
            }
        )
        r2, _ = Route.objects.get_or_create(
            title='Route 2: DHA Phase 5 - Cantt - Campus',
            defaults={
                'start_point': 'DHA Phase 5 Commercial',
                'end_point': 'Main Campus Gate B',
                'monthly_fare': Decimal('4200.00'),
                'is_active': True,
            }
        )

        stop1, _ = RouteStop.objects.get_or_create(route=r1, stop_name='Liberty Roundabout', stop_order=1, defaults={'pickup_time': '07:15:00', 'drop_time': '14:15:00'})
        stop2, _ = RouteStop.objects.get_or_create(route=r1, stop_name='Model Town Link Road', stop_order=2, defaults={'pickup_time': '07:30:00', 'drop_time': '14:00:00'})
        stop3, _ = RouteStop.objects.get_or_create(route=r2, stop_name='DHA Y-Block', stop_order=1, defaults={'pickup_time': '07:10:00', 'drop_time': '14:25:00'})

        students = list(Student.objects.all()[:5])
        if students:
            StudentTransportAllocation.objects.get_or_create(
                student=students[0],
                defaults={
                    'vehicle': v1,
                    'route': r1,
                    'stop': stop1,
                    'start_date': timezone.now().date(),
                    'monthly_fee': Decimal('3500.00'),
                    'status': StudentTransportAllocation.Status.ACTIVE,
                }
            )
            if len(students) > 1:
                StudentTransportAllocation.objects.get_or_create(
                    student=students[1],
                    defaults={
                        'vehicle': v2,
                        'route': r2,
                        'stop': stop3,
                        'start_date': timezone.now().date(),
                        'monthly_fee': Decimal('4200.00'),
                        'status': StudentTransportAllocation.Status.ACTIVE,
                    }
                )

        # 2. Library Categories & Books
        cat_sci, _ = BookCategory.objects.get_or_create(name='Science & Technology', defaults={'code': 'SCI', 'description': 'Physics, Chemistry, Biology & IT'})
        if not cat_sci.code:
            cat_sci.code = 'SCI'
            cat_sci.save()
        cat_lit, _ = BookCategory.objects.get_or_create(name='Literature & Languages', defaults={'code': 'LIT', 'description': 'English & Urdu Prose & Poetry'})
        if not cat_lit.code:
            cat_lit.code = 'LIT'
            cat_lit.save()
        cat_hist, _ = BookCategory.objects.get_or_create(name='History & Islamic Studies', defaults={'code': 'HIS', 'description': 'Pakistan Studies & Islamic History'})
        if not cat_hist.code:
            cat_hist.code = 'HIS'
            cat_hist.save()

        b1, _ = Book.objects.get_or_create(
            isbn='978-019906001',
            defaults={
                'title': 'Oxford Secondary English Course Grade 9',
                'author': 'Rachel Redford',
                'category': cat_lit,
                'publisher': 'Oxford University Press',
                'rack_location': 'Shelf A-3',
                'total_copies': 25,
                'available_copies': 23,
                'price': Decimal('850.00')
            }
        )
        b2, _ = Book.objects.get_or_create(
            isbn='978-019906002',
            defaults={
                'title': 'Conceptual Physics for High School',
                'author': 'Paul G. Hewitt',
                'category': cat_sci,
                'publisher': 'Pearson Education',
                'rack_location': 'Shelf B-1',
                'total_copies': 18,
                'available_copies': 17,
                'price': Decimal('1450.00')
            }
        )
        b3, _ = Book.objects.get_or_create(
            isbn='978-019906003',
            defaults={
                'title': 'Tazkira-e-Urdu Adab',
                'author': 'Prof. Anwar Sadeed',
                'category': cat_lit,
                'publisher': 'National Book Foundation',
                'rack_location': 'Shelf C-2',
                'total_copies': 12,
                'available_copies': 12,
                'price': Decimal('600.00')
            }
        )

        if students and admin_user:
            BookIssue.objects.get_or_create(
                book=b1,
                student=students[0],
                defaults={
                    'issued_by': admin_user,
                    'issue_date': timezone.now().date() - timedelta(days=5),
                    'due_date': timezone.now().date() + timedelta(days=9),
                    'status': BookIssue.Status.ISSUED,
                }
            )

        # 3. Inventory Items & Suppliers
        s1, _ = Supplier.objects.get_or_create(
            name='Al-Madina Educational Stationers',
            defaults={
                'contact_person': 'Sheikh Farooq',
                'phone': '0300-5544332',
                'email': 'almadina.books@example.com',
                'address': 'Urdu Bazaar, Lahore'
            }
        )
        s2, _ = Supplier.objects.get_or_create(
            name='Pak Scientific Equipment Suppliers',
            defaults={
                'contact_person': 'Engr. Kamran Khan',
                'phone': '0321-4433221',
                'email': 'sales@pakscientific.com',
                'address': 'Anarkali Commercial Zone, Lahore'
            }
        )

        icat_stat, _ = ItemCategory.objects.get_or_create(name='Office & Printing Stationery')
        icat_lab, _ = ItemCategory.objects.get_or_create(name='Laboratory Glassware & Chemicals')
        icat_clean, _ = ItemCategory.objects.get_or_create(name='Cleaning & Janitorial Supplies')

        i1, _ = InventoryItem.objects.get_or_create(
            item_code='STAT-A4-80G',
            defaults={
                'name': 'Double A A4 80GSM Paper Reams',
                'category': icat_stat,
                'quantity_in_stock': 45,
                'min_reorder_level': 10,
                'unit': 'REAM',
                'unit_price': Decimal('1250.00'),
                'location': 'Main Admin Store Shelf 1'
            }
        )
        i2, _ = InventoryItem.objects.get_or_create(
            item_code='LAB-TEST-TUBE-50',
            defaults={
                'name': 'Borosilicate Glass Test Tubes 50ml',
                'category': icat_lab,
                'quantity_in_stock': 120,
                'min_reorder_level': 30,
                'unit': 'PCS',
                'unit_price': Decimal('85.00'),
                'location': 'Chemistry Lab Store Cabinet 3'
            }
        )
        i3, _ = InventoryItem.objects.get_or_create(
            item_code='STAT-WB-MRK-BLK',
            defaults={
                'name': 'Dollar Whiteboard Markers (Black)',
                'category': icat_stat,
                'quantity_in_stock': 8,
                'min_reorder_level': 15,
                'unit': 'BOX',
                'unit_price': Decimal('720.00'),
                'location': 'Staff Room Supplies Box'
            }
        )

        StockTransaction.objects.get_or_create(
            item=i1,
            reference_number='PO-9921',
            defaults={
                'transaction_type': StockTransaction.Type.IN,
                'quantity': 50,
                'unit_price': Decimal('1250.00'),
                'supplier': s1,
                'transaction_date': timezone.now().date() - timedelta(days=10),
                'created_by': admin_user,
                'notes': 'Quarterly paper bulk purchase order'
            }
        )

        self.stdout.write(self.style.SUCCESS("[SUCCESS] Sprint 7 demonstration data seeded successfully!"))
