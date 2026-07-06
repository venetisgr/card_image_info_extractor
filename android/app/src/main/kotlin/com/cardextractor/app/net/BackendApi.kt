package com.cardextractor.app.net

import com.cardextractor.app.BuildConfig
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.util.concurrent.TimeUnit

/** Our FastAPI backend (see backend/): extraction + PSA enrichment. */
interface BackendApi {

    @Multipart
    @POST("extract")
    suspend fun extract(
        @Part front: MultipartBody.Part,
        @Part back: MultipartBody.Part?,
    ): ResponseBody

    companion object {
        fun create(baseUrl: String = BuildConfig.BACKEND_BASE_URL): BackendApi {
            val client = OkHttpClient.Builder()
                // Claude extraction takes ~10-20s per scan.
                .readTimeout(120, TimeUnit.SECONDS)
                .addInterceptor(
                    HttpLoggingInterceptor().apply {
                        level = HttpLoggingInterceptor.Level.BASIC
                    }
                )
                .build()
            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .build()
                .create(BackendApi::class.java)
        }
    }
}
