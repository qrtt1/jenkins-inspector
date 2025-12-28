def test_auth_success(run_jenkee):
    """測試成功的認證情境"""
    # Arrange: 使用正確的 Jenkins 認證資訊（由 fixture 提供）

    # Act: 執行 auth 指令
    result = run_jenkee.run("auth")

    # Assert: 驗證認證成功並且是正確的測試用戶
    assert result.returncode == 0
    assert "Authenticated as:" in result.stdout or "✓" in result.stdout
    # 驗證是我們建立的 jenkins-test 用戶
    assert "jenkins-test" in result.stdout


def test_auth_failure_with_wrong_token(run_jenkee_bad_auth):
    """測試錯誤 token 導致認證失敗"""
    # Arrange: 使用錯誤的認證資訊（由 fixture 提供）

    # Act: 執行 auth 指令，預期失敗
    result = run_jenkee_bad_auth.build_command("auth").must_fail().run()

    # Assert: 驗證認證失敗並有錯誤訊息
    assert result.returncode != 0
    assert "Authentication failed" in result.stderr or "failed" in result.stderr.lower()


def test_auth_output_format(run_jenkee):
    """測試 auth 輸出格式包含必要資訊"""
    # Arrange: 使用正確的認證資訊

    # Act: 執行 auth 指令
    result = run_jenkee.run("auth")

    # Assert: 驗證輸出包含認證相關關鍵字
    assert result.returncode == 0
    output = result.stdout.lower()
    assert any(keyword in output for keyword in ["authenticated", "✓", "success"])


def test_auth_with_timeout(run_jenkee):
    """測試 auth 指令可以設定 timeout"""
    # Arrange: 設定 30 秒 timeout

    # Act: 執行 auth 指令並設定 timeout
    result = run_jenkee.build_command("auth").with_timeout(30).run()

    # Assert: 驗證在 timeout 內完成認證
    assert result.returncode == 0


def test_auth_idempotent(run_jenkee):
    """測試 auth 指令可以重複執行（冪等性）"""
    # Arrange: 準備重複執行相同指令

    # Act: 執行兩次 auth 指令
    result1 = run_jenkee.run("auth")
    result2 = run_jenkee.run("auth")

    # Assert: 兩次執行都成功且結果一致
    assert result1.returncode == 0
    assert result2.returncode == 0
    assert "Authenticated" in result1.stdout or "✓" in result1.stdout
    assert "Authenticated" in result2.stdout or "✓" in result2.stdout
