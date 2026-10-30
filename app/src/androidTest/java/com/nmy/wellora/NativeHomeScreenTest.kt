package com.nmy.wellora

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test

class NativeHomeScreenTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun homeShowsNativePrototypeContent() {
        composeRule.onNodeWithText("Home").assertIsDisplayed()
        composeRule.onNodeWithText("上传报告").assertIsDisplayed()
        composeRule.onNodeWithText("报告对比").assertIsDisplayed()
        composeRule.onNodeWithText("首页").assertIsDisplayed()
        composeRule.onNodeWithText("健康档案").assertIsDisplayed()
    }

    @Test
    fun elderModeToggleUpdatesItsLabel() {
        composeRule.onNodeWithText("长辈模式").performClick()
        composeRule.onNodeWithText("标准模式").assertIsDisplayed()
    }

    @Test
    fun featureCardOpensNativePlaceholderRoute() {
        composeRule.onNodeWithText("上传报告").performClick()
        composeRule.onNodeWithText("此页面尚未实现；当前仅验证原生 Compose 导航。").assertIsDisplayed()
    }

    @Test
    fun bottomNavigationOpensNativePlaceholderRoute() {
        composeRule.onNodeWithText("健康档案").performClick()
        composeRule.onNodeWithText("原生 Compose 路由已就绪，健康档案页面将在后续迭代实现。").assertIsDisplayed()
    }
}
