import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, InjectionToken, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';
import { ApiProblemError, ProblemDetails, QuestionResponse } from './api.models';

export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', { providedIn: 'root', factory: () => '' });

function isProblem(body: unknown): body is ProblemDetails {
  if (typeof body !== 'object' || body === null) return false;
  const b = body as Record<string, unknown>;
  return typeof b['title'] === 'string' && typeof b['status'] === 'number';
}

function toProblemError(err: unknown): ApiProblemError {
  if (err instanceof HttpErrorResponse) {
    if (isProblem(err.error)) return new ApiProblemError(err.error);
    return new ApiProblemError({
      type: 'about:blank',
      title: err.status === 0 ? 'Network error' : err.statusText || 'Request failed',
      status: err.status,
    });
  }
  return new ApiProblemError({ type: 'about:blank', title: 'Unexpected error', status: 0 });
}

@Injectable({ providedIn: 'root' })
export class QuestionsApi {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL);

  ask(audio: Blob): Observable<QuestionResponse> {
    const form = new FormData();
    form.append('audio', audio, 'question.webm');
    return this.http
      .post<QuestionResponse>(`${this.base}/v1/questions`, form)
      .pipe(catchError((e: unknown) => throwError(() => toProblemError(e))));
  }
}
