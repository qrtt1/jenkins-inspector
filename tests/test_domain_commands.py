"""
測試 domain list 指令

涵蓋指令：
- domain list
"""
import re
import uuid


def parse_domain_list(stdout: str) -> dict:
    """解析 domain list 輸出"""
    domains = {}
    for line in stdout.splitlines():
        match = re.match(r'^\s{2}(.+?)\s{2}(.+)\s\((\d+)\scredential', line)
        if match:
            name = match.group(1).strip()
            description = match.group(2).strip()
            count = int(match.group(3))
            domains[name] = {"description": description, "count": count}
    return domains


def parse_domain_total(stdout: str) -> int:
    """解析 domain list 總數"""
    for line in stdout.splitlines():
        match = re.match(r'^Total:\s+(\d+)\s+domains$', line.strip())
        if match:
            return int(match.group(1))
    return 0


def test_domain_list_basic(run_jenkee_authed):
    """測試列出 domain 清單與 credential 數量"""
    result = run_jenkee_authed.run("domain", "list")

    assert result.returncode == 0, f"domain list should succeed, got: {result.stderr}"
    assert "Available domains" in result.stdout

    domains = parse_domain_list(result.stdout)
    total = parse_domain_total(result.stdout)

    assert total == len(domains), "Total domains should match parsed output"

    assert "(global)" in domains, "Should include global domain"
    assert "staging" in domains, "Should include staging domain"
    assert "production" in domains, "Should include production domain"

    assert "Global credentials domain" in domains["(global)"]["description"]
    assert "Staging environment credentials" in domains["staging"]["description"]
    assert "Production environment credentials" in domains["production"]["description"]

    assert domains["staging"]["count"] >= 1, "Staging domain should have credentials"
    assert domains["production"]["count"] == 0, "Production domain should be empty"
    assert domains["(global)"]["count"] >= 3, "Global domain should include test credentials"


def test_domain_create_basic(run_jenkee_authed):
    """測試建立 domain"""
    domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
    description = "Test domain created by tests"

    result = run_jenkee_authed.run(
        "domain",
        "create",
        domain_name,
        "--description",
        description,
        "--yes-i-really-mean-it",
    )

    assert result.returncode == 0, f"domain create should succeed, got: {result.stderr}"
    assert f"Created domain: {domain_name}" in result.stdout

    list_result = run_jenkee_authed.run("domain", "list")
    domains = parse_domain_list(list_result.stdout)

    assert domain_name in domains, "Created domain should appear in list output"
    assert domains[domain_name]["description"] == description
    assert domains[domain_name]["count"] == 0
