"""
Load users and client data into the system
"""
from app import app, db
from models import User, UserRole, Client
from werkzeug.security import generate_password_hash

def create_users():
    """Create the specified users"""
    users_data = [
        {
            'email': 'jason.skiljan@accellis.com',
            'first_name': 'Jason',
            'last_name': 'Skiljan',
            'role': UserRole.VCIO,
            'notes': 'vCIO'
        },
        {
            'email': 'justin.hothem@accellis.com',
            'first_name': 'Justin',
            'last_name': 'Hothem', 
            'role': UserRole.TAM,
            'notes': 'Technical Account Manager'
        },
        {
            'email': 'zach.berrie@accellis.com',
            'first_name': 'Zach',
            'last_name': 'Berrie',
            'role': UserRole.TAM,
            'notes': 'Technical Account Manager'
        },
        {
            'email': 'abbey.dewitt@accellis.com',
            'first_name': 'Abbey',
            'last_name': 'DeWitt',
            'role': UserRole.ADMIN,
            'notes': 'ADMIN'
        },
        {
            'email': 'brian.guscott@accellis.com',
            'first_name': 'Brian',
            'last_name': 'Guscott',
            'role': UserRole.ADMIN,
            'notes': 'ADMIN'
        }
    ]
    
    with app.app_context():
        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"User {user_data['email']} already exists")
                continue
                
            # Create user with default password
            user = User(
                id=f"user_{len(created_users) + 1:03d}",
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                password_hash=generate_password_hash('password123'),  # Default password
                is_active=True
            )
            
            db.session.add(user)
            created_users.append(user)
            print(f"Created user: {user.email} ({user_data['notes']})")
        
        try:
            db.session.commit()
            print(f"Successfully created {len(created_users)} users")
            return created_users
        except Exception as e:
            db.session.rollback()
            print(f"Error creating users: {e}")
            return []

def load_client_data():
    """Load client data from the provided file"""
    client_data = [
        # Alex Ivanov's clients
        {'name': 'Brooks & Stafford', 'account_manager': 'Alex Ivanov', 'contact': 'Greg Kunze', 'email': 'gkunze@brooks-stafford.com', 'phone': '(440) 667-8749'},
        {'name': 'Cramer & Peavy', 'account_manager': 'Alex Ivanov', 'contact': 'Jim Peavy', 'email': 'jim@cramerpeavy.com', 'phone': '(770) 227-4955'},
        {'name': "Dave's Supermarkets Inc.", 'account_manager': 'Alex Ivanov', 'contact': 'William Weinberg', 'email': 'wweinberg@davesmrkt.com', 'phone': '(216) 763-3194'},
        {'name': 'Dover', 'account_manager': 'Alex Ivanov', 'contact': 'Julia Maddy', 'email': 'julia@dovertank.com', 'phone': '(330) 364-7989'},
        {'name': 'Graphite Sales, Inc.', 'account_manager': 'Alex Ivanov', 'contact': 'Mike Slabe', 'email': 'mslabe@graphitesales.com', 'phone': '(440) 543-8221 ext. 513'},
        {'name': 'Harrington, Hoppe & Mitchell, Ltd.', 'account_manager': 'Alex Ivanov', 'contact': 'Jennifer DeRubba', 'email': 'JDeRubba@HHMLAW.com', 'phone': '(330) 337-6586'},
        {'name': 'IT Exchangenet', 'account_manager': 'Alex Ivanov', 'contact': 'Dylan Tober', 'email': 'dtober@itexchangenet.com', 'phone': '678-642-0500'},
        {'name': 'Kaman & Cusimano', 'account_manager': 'Alex Ivanov', 'contact': 'Jay Cusimano', 'email': 'jcusimano@kamancus.com', 'phone': '(216) 696-0650'},
        {'name': 'LCBDD', 'account_manager': 'Alex Ivanov', 'contact': 'Curtis Ellis', 'email': 'curtis.ellis@lakebdd.org', 'phone': '(440) 350-5100'},
        {'name': 'Lorain County Law Library', 'account_manager': 'Alex Ivanov', 'contact': 'J. Zachary Springer', 'email': 'zspringer@lorainlawlib.org', 'phone': '(216) 832-5392'},
        {'name': 'Mussun', 'account_manager': 'Alex Ivanov', 'contact': 'Katie Blackmur', 'email': 'kblackmur@mussun.com', 'phone': '(216) 431-5088'},
        {'name': 'Singerman, Mills, Desberg & Kauntz Co., L.P.A.', 'account_manager': 'Alex Ivanov', 'contact': 'Brian Falkowski', 'email': 'bfalkowski@smdk.com', 'phone': '(216) 292-5807'},
        {'name': 'Southwest Companies Inc', 'account_manager': 'Alex Ivanov', 'contact': 'Anthony Fyffe', 'email': 'afyffe@southwestcoinc.com', 'phone': '(216) 642-1195'},
        {'name': 'Sterling Associates Group', 'account_manager': 'Alex Ivanov', 'contact': 'Jacob Dar', 'email': 'jacob.dar@sterlingassociates.com', 'phone': '(440) 684-9850'},
        {'name': 'The Law Office of Michelle A. Lawless LLC', 'account_manager': 'Alex Ivanov', 'contact': 'Michelle A. Lawless', 'email': 'michelle@malfamilylaw.com', 'phone': '(312) 605-9064'},
        
        # Jason Skiljan's clients
        {'name': 'Alcon', 'account_manager': 'Jason Skiljan', 'contact': 'Jacob Vadini', 'email': 'jvadini@alconindustries.com', 'phone': '(216) 961-1100 ext. 225'},
        {'name': 'ARC Drilling', 'account_manager': 'Jason Skiljan', 'contact': 'Jason Busse', 'email': 'jbusse@arcdrilling.com', 'phone': '(216) 525-0920 ext. 408'},
        {'name': 'Caruso', 'account_manager': 'Jason Skiljan', 'contact': 'Michael Caruso', 'email': 'michael@carusoscoffee.com', 'phone': '(440) 546-0901'},
        {'name': 'Climaco', 'account_manager': 'Jason Skiljan', 'contact': 'Cindy Parisi', 'email': 'clpari@climacolaw.com', 'phone': '(216) 522-0265'},
        {'name': 'Inland Counties Legal Services', 'account_manager': 'Jason Skiljan', 'contact': 'Jaime Cartagena', 'email': 'jcartagena@icls.org', 'phone': '(951) 320-7503'},
        {'name': 'Kitroser, Lewis and Mighdoll, LLC', 'account_manager': 'Jason Skiljan', 'contact': 'Jade Sih', 'email': 'jade@kitroserlaw.com', 'phone': '(772) 362-9570'},
        {'name': 'Legal Aid - Bluegrass', 'account_manager': 'Jason Skiljan', 'contact': 'Brenda Combs', 'email': 'bcombs@lablaw.org', 'phone': '(606) 776-6586'},
        {'name': 'Legal Aid Society of Cleveland', 'account_manager': 'Jason Skiljan', 'contact': 'Colleen Cotter', 'email': 'Ccotter@lasclev.org', 'phone': '(216) 861-5500'},
        {'name': 'Legal Aid Society of Northeast Ohio', 'account_manager': 'Jason Skiljan', 'contact': 'Roslyn Quarto', 'email': 'rquarto@lasclev.org', 'phone': ''},
        {'name': 'Mansour Gavin LPA', 'account_manager': 'Jason Skiljan', 'contact': 'Kimberly Szabo', 'email': 'kszabo@mggmlpa.com', 'phone': '(216) 523-1500'},
        {'name': 'Misco', 'account_manager': 'Jason Skiljan', 'contact': 'Damon Sweeney', 'email': 'dsweeney@misco.com', 'phone': '(440) 349-1500'},
        {'name': 'RMS Investment Corporation', 'account_manager': 'Jason Skiljan', 'contact': 'Melanie Lucas', 'email': 'mlucas@rmsco.com', 'phone': '(216) 233-5481'},
        {'name': 'Root', 'account_manager': 'Jason Skiljan', 'contact': 'Cassie Locke', 'email': 'clocke@rootintegration.com', 'phone': '(216) 282-7470'},
        {'name': 'Tavens', 'account_manager': 'Jason Skiljan', 'contact': 'Vicki Walters', 'email': 'vwalters@tavens.com', 'phone': '(216) 883-3333'},
        {'name': 'Vaudra', 'account_manager': 'Jason Skiljan', 'contact': 'Matthew Hewlett', 'email': 'mnh@vaudra.com', 'phone': '(704) 895-3939'},
        {'name': 'Weston Hurd LLP', 'account_manager': 'Jason Skiljan', 'contact': 'Randy Wetzel', 'email': 'rwetzel@westonhurd.com', 'phone': '(216) 687-3275'},
        {'name': 'Yacobozzi', 'account_manager': 'Jason Skiljan', 'contact': 'Eleni A. ("Eleana") Drakatos', 'email': 'edrakatos@ydlegal.com', 'phone': '(614) 443-2800 ext. 2002'},
        
        # Justin Hothem's clients
        {'name': 'Amark Logistics, Inc.', 'account_manager': 'Justin Hothem', 'contact': 'Marc Houlas', 'email': 'marc.houlas@amarklogistics.com', 'phone': '(440) 732-0555'},
        {'name': 'Amin, Turocy & Watson, LLP', 'account_manager': 'Justin Hothem', 'contact': 'Heather McKee', 'email': 'HMcKee@thepatentattorneys.com', 'phone': '(216) 696-8730 ext. 797'},
        {'name': 'Beachwood Plastic Surgery', 'account_manager': 'Justin Hothem', 'contact': 'Brooke Bungard', 'email': 'bbungard@drgoldman.com', 'phone': '(440) 871-8899'},
        {'name': 'Caravus', 'account_manager': 'Justin Hothem', 'contact': 'J.J. Flotken', 'email': 'flotkenj@caravus.com', 'phone': '(314) 259-5047'},
        {'name': 'Cefaratti Group', 'account_manager': 'Justin Hothem', 'contact': 'Kim Fleming', 'email': 'kim@cefgroup.com', 'phone': '(216) 696-1161 ext. 204'},
        {'name': 'Checkpoint Surgical', 'account_manager': 'Justin Hothem', 'contact': 'Ben Cottrill', 'email': 'bcottrill@checkpointsurgical.com', 'phone': '(216) 832-9286'},
        {'name': 'City Club of Cleveland', 'account_manager': 'Justin Hothem', 'contact': 'Julie Kelly', 'email': 'jkelly@cityclub.org', 'phone': '(216) 621-0082'},
        {'name': 'Firestone Federal Credit Union', 'account_manager': 'Justin Hothem', 'contact': 'Beth Morvai', 'email': 'beth@fstonecu.com', 'phone': '(234) 352-1095 ext. 220'},
        {'name': 'Highland Consulting Associates', 'account_manager': 'Justin Hothem', 'contact': 'Sue Wohleber', 'email': 'swohleber@highlandusa.net', 'phone': '(440) 808-1500'},
        {'name': 'NCCH', 'account_manager': 'Justin Hothem', 'contact': 'Nick Stroup', 'email': 'nstroup@ncch.org', 'phone': '(216) 662-1880'},
        {'name': 'Nager Romaine & Schneiberg Co', 'account_manager': 'Justin Hothem', 'contact': 'Rob Bordonaro', 'email': 'rbordonaro@nrsinjurylaw.com', 'phone': '(855) 468-4878'},
        {'name': 'Ohio Title', 'account_manager': 'Justin Hothem', 'contact': 'Melanie Turner', 'email': 'mturner@ohiotitlecorp.com', 'phone': '(330) 523-9478'},
        {'name': 'Paran Management', 'account_manager': 'Justin Hothem', 'contact': 'Mark Zielinski', 'email': 'mzielinski@paranmgt.com', 'phone': '(216) 921-5663 ext. 113'},
        {'name': 'Pradco', 'account_manager': 'Justin Hothem', 'contact': 'Paul Cimino', 'email': 'pcimino@pradco.com', 'phone': '(440) 337-4700'},
        {'name': 'Ritzler, Coughlin & Paglia', 'account_manager': 'Justin Hothem', 'contact': 'Jennifer Garibaldi', 'email': 'jgaribaldi@rcp-attorneys.com', 'phone': '(216)2412513 ext.111'},
        {'name': 'Spangenberg', 'account_manager': 'Justin Hothem', 'contact': 'Joshua Podsedly', 'email': 'jpodsedly@spanglaw.com', 'phone': '(216) 696-3232'},
        
        # Zach Berrie's clients
        {'name': 'Berkman, Gordon, Murray & DeVan', 'account_manager': 'Zach Berrie', 'contact': 'Amy Hudson', 'email': 'ahudson@bgmdlaw.com', 'phone': '(216) 781-5245'},
        {'name': 'Bugbee', 'account_manager': 'Zach Berrie', 'contact': 'Laurie Moran', 'email': 'lmoran@bugbeelawyers.com', 'phone': '(419)2145512'},
        {'name': 'Charna E. Sherman Law Offices Co., LPA', 'account_manager': 'Zach Berrie', 'contact': 'Charna Sherman', 'email': 'ces@charnaunlimited.com', 'phone': '(216) 453-0808'},
        {'name': 'Collins Cole', 'account_manager': 'Zach Berrie', 'contact': 'Claudia Miller', 'email': 'cmiller@cogovlaw.com', 'phone': '(720) 617-6006'},
        {'name': 'Frantz Medical', 'account_manager': 'Zach Berrie', 'contact': 'Kathy Vance', 'email': 'kvance@frantzgroup.com', 'phone': '(440) 974-2308'},
        {'name': 'Haber', 'account_manager': 'Zach Berrie', 'contact': 'Richard  Haber', 'email': 'rhaber@haberllp.com', 'phone': '(216) 402-8142'},
        {'name': 'Industrial Profile Systems', 'account_manager': 'Zach Berrie', 'contact': 'Jon Kasberg', 'email': 'jkasberg@industrialprofile.com', 'phone': '(440) 227-4690'},
        {'name': 'Life Equity', 'account_manager': 'Zach Berrie', 'contact': 'Christian Kennedy', 'email': 'ckennedy@coventry.com', 'phone': '(330) 655-7500'},
        {'name': 'RCG Tax Partners', 'account_manager': 'Zach Berrie', 'contact': 'Ron Antal', 'email': 'Ron.Antal@rcg-inc.com', 'phone': '(330) 812-3611 ext. 107'},
        {'name': 'Sager Company', 'account_manager': 'Zach Berrie', 'contact': 'Michael Gerbasi', 'email': 'mgerbasi@sagercompany.com', 'phone': '(216) 536-5311'},
        {'name': 'Scott Scriven LLP', 'account_manager': 'Zach Berrie', 'contact': 'Carol Durant', 'email': 'carol@scottscrivenlaw.com', 'phone': '(614) 827-6401'},
        {'name': 'Sonkin & Koberna, LLC', 'account_manager': 'Zach Berrie', 'contact': 'Megan Pacheco', 'email': 'mpacheco@sklawllc.com', 'phone': '(216) 514-8300'},
        {'name': 'Thrasher, Dinsmore, & Dolan', 'account_manager': 'Zach Berrie', 'contact': 'Scott Sumner', 'email': 'SSumner@tddlaw.com', 'phone': '(216) 534-1855'}
    ]
    
    with app.app_context():
        created_clients = []
        for client_info in client_data:
            # Check if client already exists
            existing_client = Client.query.filter_by(name=client_info['name']).first()
            if existing_client:
                print(f"Client {client_info['name']} already exists")
                continue
                
            # Truncate phone number to fit database constraint (20 chars max)
            phone = client_info['phone'][:19] if client_info['phone'] else ''
            
            # Create client
            client = Client(
                name=client_info['name'],
                contact_name=client_info['contact'],
                contact_email=client_info['email'],
                contact_phone=phone,
                description=f"Managed by {client_info['account_manager']}",
                industry="Professional Services",  # Default industry based on the data
                is_active=True
            )
            
            db.session.add(client)
            created_clients.append(client)
            print(f"Created client: {client.name} (Contact: {client.contact_name})")
        
        try:
            db.session.commit()
            print(f"Successfully created {len(created_clients)} clients")
            return created_clients
        except Exception as e:
            db.session.rollback()
            print(f"Error creating clients: {e}")
            return []

if __name__ == "__main__":
    print("Creating users...")
    create_users()
    print("\nLoading client data...")
    load_client_data()
    print("\nData loading complete!")