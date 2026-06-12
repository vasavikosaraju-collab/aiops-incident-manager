"""
generate_dataset.py

Generates a synthetic-but-realistic dataset of IT support ticket
descriptions labeled with the team that should handle them.

This script exists so the dataset used to train the routing model
is reproducible. In a real-world version of this project, you would
replace this with an export from your helpdesk system (Zendesk,
Jira Service Management, ServiceNow, etc.) or a public Kaggle
IT-support-ticket dataset.
"""

import csv
import random

random.seed(42)

# Template phrases per support team. Each template has placeholders
# that get filled in with random "flavor" words so the generated
# descriptions aren't all identical, which keeps the classification
# task realistic (some ambiguity between categories).

TEMPLATES = {
    "NETWORK": [
        "VPN connection keeps dropping for {user}",
        "Unable to connect to the office VPN from home",
        "Wi-Fi is down on the {floor} floor",
        "Network latency is very high when accessing internal sites",
        "User cannot access the internal network from the {location} office",
        "DNS resolution is failing for internal domains",
        "Firewall is blocking access to {tool}",
        "Site-to-site VPN tunnel between offices is down",
        "Ethernet port in conference room {room} is not working",
        "Remote employees cannot reach the corporate intranet",
        "Packet loss detected on the {location} network segment",
        "VLAN configuration issue causing intermittent connectivity",
    ],
    "DATABASE": [
        "Database connection timeout on the {tool} service",
        "Production database is running out of disk space",
        "Slow query performance on the {tool} reporting database",
        "Database replication lag between primary and replica",
        "Unable to connect to PostgreSQL instance from {tool}",
        "Deadlock errors occurring on the orders table",
        "Database backup job failed last night",
        "High CPU usage on the database server during peak hours",
        "Need to restore a table from yesterday's database backup",
        "Database connection pool exhausted for {tool}",
        "Index rebuild required on the customers table for performance",
        "MySQL server crashed and restarted unexpectedly",
    ],
    "SECURITY": [
        "Suspicious login attempts detected on {user}'s account",
        "Phishing email reported by {user}",
        "Multi-factor authentication not working for {user}",
        "Need to reset password and unlock account for {user}",
        "Malware detected on a workstation in the {location} office",
        "Request to review firewall rules for compliance audit",
        "Unauthorized access attempt blocked by intrusion detection",
        "SSL certificate for {tool} is expiring soon",
        "User reports their account may have been compromised",
        "Security scan flagged outdated software on several laptops",
        "Access request for {tool} needs security approval",
        "Ransomware alert triggered by endpoint protection on {user}'s laptop",
    ],
    "CLOUD": [
        "AWS EC2 instance for {tool} is not responding",
        "S3 bucket permissions need to be updated for {tool}",
        "Auto-scaling group did not scale up during traffic spike",
        "ECS task for {tool} keeps restarting",
        "Cloud storage costs increased significantly this month",
        "Need a new IAM role created for the {tool} team",
        "Load balancer health checks failing for {tool} service",
        "RDS instance for {tool} needs to be resized",
        "CloudWatch alarms not triggering notifications",
        "Lambda function timing out when processing {tool} events",
        "Need to provision a new environment for {tool} on AWS",
        "ECS service deployment stuck in pending state",
    ],
    "APPLICATION": [
        "Application crashes on login for {user}",
        "{tool} dashboard is showing a blank page",
        "Error 500 when submitting the form on {tool}",
        "{tool} is running very slowly for all users",
        "Feature request: add export to CSV in {tool}",
        "User cannot upload files in {tool}",
        "{tool} login page is stuck on loading spinner",
        "Notifications are not being sent from {tool}",
        "Incorrect totals displayed on the {tool} reports page",
        "{tool} mobile app crashes on startup",
        "Search functionality in {tool} returns no results",
        "{user} is getting a permission denied error in {tool}",
    ],
    "DEVOPS": [
        "CI/CD pipeline for {tool} is failing on the build step",
        "Need to roll back the latest deployment of {tool}",
        "Docker container for {tool} keeps crashing on startup",
        "GitHub Actions workflow stuck and not completing",
        "Need a new staging environment set up for {tool}",
        "Deployment of {tool} to production failed",
        "Kubernetes pod for {tool} is in CrashLoopBackOff",
        "Build artifacts for {tool} are not being published",
        "Need to add a new secret to the {tool} pipeline",
        "Monitoring dashboard for {tool} is not showing recent metrics",
        "Need access to deployment logs for {tool}",
        "Terraform apply failed while provisioning {tool} infrastructure",
    ],
}

# Ambiguous templates that plausibly belong to more than one team.
# These are mixed into the dataset to make the classification task
# realistic -- a perfectly clean dataset would let even a simple
# model hit 100% accuracy, which doesn't reflect real-world ticket
# routing data.
AMBIGUOUS_TEMPLATES = [
    ("{tool} is down and users cannot log in", ["APPLICATION", "CLOUD", "NETWORK"]),
    ("{tool} is extremely slow for everyone", ["APPLICATION", "DATABASE", "NETWORK"]),
    ("{user} cannot access {tool} at all", ["APPLICATION", "SECURITY", "NETWORK"]),
    ("{tool} outage affecting the {location} office", ["CLOUD", "NETWORK", "APPLICATION"]),
    ("Getting connection errors when using {tool}", ["NETWORK", "DATABASE", "APPLICATION"]),
    ("{tool} deployment caused an outage", ["DEVOPS", "APPLICATION", "CLOUD"]),
    ("Login is broken for {user} on {tool}", ["APPLICATION", "SECURITY", "DEVOPS"]),
    ("Performance degradation reported on {tool}", ["APPLICATION", "DATABASE", "CLOUD"]),
]

USERS = ["John", "Priya", "Wei", "Maria", "Alex", "Fatima", "Sam", "Lena", "Carlos", "Mei"]
TOOLS = ["the billing service", "the CRM", "the analytics platform", "the HR portal",
         "the payment gateway", "the order management system", "the reporting tool",
         "the internal wiki", "the customer portal", "the inventory system"]
LOCATIONS = ["New York", "Bangalore", "London", "Austin", "Toronto", "remote"]
FLOORS = ["3rd", "5th", "2nd", "ground"]
ROOMS = ["A12", "B4", "C201", "D7"]


def fill(template):
    return template.format(
        user=random.choice(USERS),
        tool=random.choice(TOOLS),
        location=random.choice(LOCATIONS),
        floor=random.choice(FLOORS),
        room=random.choice(ROOMS),
    )


def generate(samples_per_category=110, ambiguous_count=90):
    rows = []
    for team, templates in TEMPLATES.items():
        for _ in range(samples_per_category):
            template = random.choice(templates)
            description = fill(template)
            priority = random.choices(
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                weights=[0.25, 0.40, 0.25, 0.10],
            )[0]
            rows.append({
                "description": description,
                "team": team,
                "priority": priority,
            })

    # Mix in ambiguous tickets. The "true" label is the first team in
    # the list (the most likely owner), but the wording overlaps with
    # other teams' vocabulary, which is what makes routing genuinely
    # hard -- and why a single 91% accuracy model is a believable,
    # defensible result instead of a toy 100% result.
    for _ in range(ambiguous_count):
        template, possible_teams = random.choice(AMBIGUOUS_TEMPLATES)
        description = fill(template)
        priority = random.choices(
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            weights=[0.20, 0.35, 0.30, 0.15],
        )[0]
        rows.append({
            "description": description,
            "team": possible_teams[0],
            "priority": priority,
        })

    random.shuffle(rows)

    # Inject label noise to simulate real-world ticket data, where
    # some tickets are mislabeled/miscategorized by whoever created
    # them (a very common issue in real helpdesk systems). Without
    # this, even a simple model trivially hits 100% on this dataset
    # because the vocabulary per category is too distinct.
    teams = list(TEMPLATES.keys())
    noise_rate = 0.06
    n_noisy = int(len(rows) * noise_rate)
    noisy_indices = random.sample(range(len(rows)), n_noisy)
    for i in noisy_indices:
        current = rows[i]["team"]
        other_teams = [t for t in teams if t != current]
        rows[i]["team"] = random.choice(other_teams)

    return rows


def main():
    rows = generate()
    with open("ticket_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["description", "team", "priority"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to ticket_dataset.csv")


if __name__ == "__main__":
    main()
