"""
Shared mock data reference lists used by all ingestion workers.
"""
import random
from datetime import date, timedelta

rng = random.Random(42)

OFFICES = [
    ("Munich HQ",     "Germany",        "Europe"),
    ("Berlin Office", "Germany",        "Europe"),
    ("London Office", "United Kingdom", "Europe"),
    ("Stockholm",     "Sweden",         "Europe"),
    ("New York",      "United States",  "Americas"),
    ("Singapore",     "Singapore",      "APAC"),
    ("Remote",        "Various",        "Global"),
]

DEPARTMENTS = [
    ("Engineering",      "Technology",  "Munich HQ"),
    ("Data Science",     "Technology",  "Munich HQ"),
    ("DevOps",           "Technology",  "Munich HQ"),
    ("Security",         "Technology",  "Munich HQ"),
    ("IT",               "Technology",  "Munich HQ"),
    ("Design",           "Product",     "Berlin Office"),
    ("Product",          "Product",     "Munich HQ"),
    ("Finance",          "Business",    "Munich HQ"),
    ("Legal",            "Business",    "London Office"),
    ("HR",               "People",      "Munich HQ"),
    ("Sales",            "Commercial",  "New York"),
    ("Marketing",        "Commercial",  "Berlin Office"),
    ("Customer Success", "Commercial",  "New York"),
    ("Operations",       "Business",    "Stockholm"),
    ("Executive",        "Leadership",  "Munich HQ"),
]

TITLES_BY_DEPT = {
    "Engineering":      ["Junior Software Engineer","Software Engineer","Senior Software Engineer","Staff Engineer","Engineering Manager"],
    "Data Science":     ["Data Analyst","Data Scientist","Senior Data Scientist","ML Engineer","Head of Data"],
    "DevOps":           ["DevOps Engineer","Senior DevOps Engineer","Platform Engineer","SRE","DevOps Lead"],
    "Security":         ["Security Analyst","Security Engineer","Senior Security Engineer","CISO"],
    "IT":               ["IT Support Specialist","Systems Administrator","IT Engineer","IT Manager","CIO"],
    "Design":           ["UI Designer","UX Designer","Senior Product Designer","Design Lead"],
    "Product":          ["Associate PM","Product Manager","Senior PM","Director of Product","CPO"],
    "Finance":          ["Financial Analyst","Senior Financial Analyst","Controller","Finance Manager","CFO"],
    "Legal":            ["Paralegal","Legal Counsel","Senior Counsel","General Counsel"],
    "HR":               ["HR Coordinator","HR Generalist","HR Business Partner","HR Manager","VP of HR"],
    "Sales":            ["SDR","Account Executive","Senior AE","Sales Manager","VP of Sales"],
    "Marketing":        ["Marketing Coordinator","Marketing Manager","Senior Marketing Manager","CMO"],
    "Customer Success": ["CS Specialist","Customer Success Manager","Senior CSM","VP of Customer Success"],
    "Operations":       ["Operations Analyst","Operations Manager","Director of Operations","COO"],
    "Executive":        ["Executive Assistant","Chief of Staff","CEO","CTO"],
}

FIRST_NAMES = [
    "Alice","Bob","Carol","Dan","Eva","Frank","Grace","Henry","Irene","James",
    "Karen","Leo","Maya","Nathan","Olivia","Paul","Quinn","Rachel","Sam","Tina",
    "Uma","Victor","Wendy","Xavier","Yara","Zach","Amelia","Brian","Clara","Derek",
    "Elena","Felix","Gina","Hugo","Isabel","Jack","Kira","Liam","Monica","Neil",
    "Omar","Petra","Raj","Sofia","Tyler","Ursula","Vince","Willow","Xena","Yusuf",
    "Zoe","Aaron","Bella","Carlos","Diana","Ethan","Fiona","George","Hana","Ian",
    "Julia","Kevin","Laura","Mike","Nadia","Oscar","Pam","Rosa","Steve","Tara",
]

LAST_NAMES = [
    "Nguyen","Martinez","Smith","Lee","Brown","Patel","Kim","Okafor","Walsh","Tran",
    "Garcia","Wilson","Anderson","Taylor","Thomas","Jackson","White","Harris","Martin","Thompson",
    "Robinson","Clark","Lewis","Walker","Hall","Allen","Young","King","Wright","Scott",
    "Green","Baker","Adams","Nelson","Carter","Mitchell","Perez","Roberts","Turner","Phillips",
    "Campbell","Parker","Evans","Edwards","Collins","Stewart","Sanchez","Morris","Rogers","Reed",
]

LAPTOP_CONFIGS = [
    ("Apple",     "MacBook Pro 14\"",      "macOS 14.4",     [16,32],   [512,1024]),
    ("Apple",     "MacBook Air 13\"",      "macOS 14.4",     [8,16],    [256,512]),
    ("Lenovo",    "ThinkPad X1 Carbon",    "Windows 11 Pro", [16,32],   [512,1024]),
    ("Lenovo",    "ThinkPad P16",          "Ubuntu 22.04",   [32,64],   [1024,2048]),
    ("Dell",      "XPS 15",               "Ubuntu 22.04",   [16,32],   [512,1024]),
    ("Dell",      "Latitude 5540",         "Windows 11 Pro", [8,16],    [256,512]),
    ("HP",        "EliteBook 840 G9",      "Windows 11 Pro", [8,16],    [256,512]),
    ("Microsoft", "Surface Laptop 5",      "Windows 11 Pro", [8,16,32], [256,512]),
]

CPU_MAP = {
    "Apple":     ["Apple M2","Apple M3 Pro","Apple M3 Max"],
    "Lenovo":    ["Intel i5-1235U","Intel i7-1365U","Intel i9-13950HX"],
    "Dell":      ["Intel i5-1345U","Intel i7-1360P","Intel i9-13900H"],
    "HP":        ["Intel i5-1235U","Intel i7-1255U"],
    "Microsoft": ["Intel i5-1245U","Intel i7-1265U"],
}

APPS = [
    ("Microsoft 365",        "Microsoft",   "Productivity",  "Enterprise"),
    ("Slack",                "Salesforce",  "Communication", "Enterprise"),
    ("Zoom",                 "Zoom",        "Communication", "Enterprise"),
    ("Google Chrome",        "Google",      "Browser",       "Free"),
    ("1Password",            "1Password",   "Security",      "Enterprise"),
    ("Okta Verify",          "Okta",        "Security",      "Enterprise"),
    ("CrowdStrike Falcon",   "CrowdStrike", "Security",      "Enterprise"),
    ("VS Code",              "Microsoft",   "Development",   "Free"),
    ("Docker Desktop",       "Docker",      "Development",   "Commercial"),
    ("Jira",                 "Atlassian",   "Project Mgmt",  "Enterprise"),
    ("Confluence",           "Atlassian",   "Documentation", "Enterprise"),
    ("Figma",                "Figma",       "Design",        "Enterprise"),
    ("Tableau Desktop",      "Salesforce",  "Analytics",     "Enterprise"),
    ("Power BI Desktop",     "Microsoft",   "Analytics",     "Enterprise"),
    ("Jupyter Notebook",     "Jupyter",     "Analytics",     "Free"),
    ("Salesforce",           "Salesforce",  "CRM",           "Enterprise"),
    ("ServiceNow",           "ServiceNow",  "ITSM",          "Enterprise"),
    ("Workday",              "Workday",     "HR",            "Enterprise"),
    ("Terraform",            "HashiCorp",   "DevOps",        "Enterprise"),
    ("AWS CLI",              "Amazon",      "Cloud",         "Free"),
    ("Datadog Agent",        "Datadog",     "Monitoring",    "Enterprise"),
    ("Cisco AnyConnect",     "Cisco",       "Security",      "Enterprise"),
    ("Zscaler Client",       "Zscaler",     "Security",      "Enterprise"),
    ("Splunk Universal Fwd", "Splunk",      "Security",      "Enterprise"),
]

TRAINING_COURSES = [
    ("Security Awareness Training",        "Security",   365),
    ("GDPR & Data Privacy",                "Compliance", 365),
    ("Anti-Harassment & Workplace Ethics", "HR",         730),
    ("Phishing Simulation",                "Security",   180),
    ("Acceptable Use Policy",              "Compliance", 365),
    ("SOC 2 Awareness",                    "Security",   365),
    ("Incident Response Basics",           "Security",   365),
    ("Code of Conduct",                    "HR",         365),
    ("Data Classification Policy",         "Security",   365),
    ("Password & MFA Best Practices",      "Security",   365),
    ("Cloud Security Fundamentals",        "Security",   365),
    ("AI & Ethics in the Workplace",       "Compliance", 365),
]

INCIDENT_TYPES = [
    ("Hardware Failure",  "Hardware",   "high"),
    ("OS Crash",          "Software",   "high"),
    ("Disk Near Full",    "Storage",    "medium"),
    ("Malware Detected",  "Security",   "critical"),
    ("Patch Missing",     "Compliance", "medium"),
    ("VPN Failure",       "Network",    "high"),
    ("Account Locked",    "Access",     "low"),
    ("Battery Swollen",   "Hardware",   "high"),
    ("Slow Performance",  "Software",   "low"),
    ("Phishing Click",    "Security",   "critical"),
    ("Backup Failed",     "Storage",    "medium"),
    ("MFA Not Enrolled",  "Security",   "high"),
    ("Unencrypted Drive", "Compliance", "critical"),
]

def rand_date(start_year=2019, end_year=2025):
    s = date(start_year, 1, 1)
    e = date(end_year, 12, 31)
    return s + timedelta(days=rng.randint(0, (e - s).days))

def weighted_choice(options, weights):
    return rng.choices(options, weights=weights, k=1)[0]
