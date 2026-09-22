package com.reportlint.app.ui.nav

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.reportlint.app.data.repository.ReportLintRepository
import com.reportlint.app.data.repository.ServerConfig
import com.reportlint.app.ui.check.CheckScreen
import com.reportlint.app.ui.review.ReviewScreen
import com.reportlint.app.ui.templates.TemplatesScreen

private object Routes {
    const val TEMPLATES = "templates"
    const val REVIEW = "review/{templateId}"
    const val CHECK = "check"
    fun review(templateId: String) = "review/$templateId"
}

@Composable
fun AppNav(repository: ReportLintRepository, serverConfig: ServerConfig) {
    val navController: NavHostController = rememberNavController()

    NavHost(navController = navController, startDestination = Routes.TEMPLATES) {
        composable(Routes.TEMPLATES) {
            TemplatesScreen(
                repository = repository,
                serverConfig = serverConfig,
                onOpenTemplate = { id -> navController.navigate(Routes.review(id)) },
                onCheckReports = { navController.navigate(Routes.CHECK) }
            )
        }
        composable(Routes.REVIEW) { backStackEntry ->
            val templateId = backStackEntry.arguments?.getString("templateId") ?: return@composable
            ReviewScreen(
                repository = repository,
                templateId = templateId,
                onBack = { navController.popBackStack() },
                onPublished = { navController.popBackStack() }
            )
        }
        composable(Routes.CHECK) {
            CheckScreen(
                repository = repository,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
