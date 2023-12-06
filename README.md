# Prisma Cloud RBAC Automation Script

## Overview

This script automates the setup of Role-Based Access Control (RBAC) configurations in Prisma Cloud, specifically tailored for Microsoft Azure subscriptions. The script leverages the Prisma Cloud API to perform the following tasks:

1. **Fetch Azure Subscription Information:**
   - Query Prisma Cloud to retrieve Azure subscription data using a predefined search query. The predefined query will look at subscription level if there are any tags that matches the key defined as "__AUTO_TEST". The script will use the Value of the same key/value pair for the RBAC configuration in this script.
   - Extract relevant information such as subscription IDs and associated tags.

   Note: "__AUTO_TEST" tag value can be replaced to match a key/value pair in Azure subscriptions.

2. **Create Account Groups:**
   - Check the existence of account groups for each Azure subscription.
   - If an account group doesn't exist, create a new one with a specific naming convention.

3. **Update User Roles:**
   - Check for the existence of user roles based on predefined tags.
   - If a user role exists, update it with the corresponding account group IDs.
   - If a user role doesn't exist, create a new one with the associated account group.

## Prerequisites

Before running the script, ensure that you have the following:

- Prisma Cloud API access credentials (username and password).
- Prisma Cloud URL.
- Necessary environment variables set for Prisma Cloud authentication.

## How to Use

1. **Clone the repository:**

   ```bash
   git clone https://github.com/danieltorandersson/prisma-cloud-rbac-automation.git
   cd prisma-cloud-rbac-automation


2. **Set up environment variables for Prisma Cloud authentication:**

    ```bash
    export PRISMACLOUD_USERNAME=your_prismacloud_username
    export PRISMACLOUD_PASSWORD=your_prismacloud_password
    export PRISMACLOUD_URL=your_prismacloud_url

3. **Run the script:**

    ```bash
    python prisma_cloud_rbac_script.py


## Notes

1. This script does not include any code for clean-up.
2. This script does not include creation of user in Prisma Cloud.


## Troubleshooting

If you encounter issues or errors while running the script, please refer to the error messages and check the Prisma Cloud documentation for API-related troubleshooting.
Disclaimer

This script is provided as-is and without warranty. Use it at your own risk. Ensure that you understand the implications of the RBAC configurations and test it in a controlled environment before applying it to production.


