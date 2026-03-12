from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="alphax_group_bi",
    version="1.1.0",
    description="Financial matrix builder for Frappe / ERPNext",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpenAI for Nooruddin Shaik",
    author_email="support@example.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
)
