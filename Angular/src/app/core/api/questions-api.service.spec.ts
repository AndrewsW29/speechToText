import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { ApiProblemError, QuestionResponse } from './api.models';
import { authInterceptor } from './auth.interceptor';
import { AuthTokenProvider } from './auth-token.provider';
import { QuestionsApi } from './questions-api.service';

const OK: QuestionResponse = {
  question_id: 'q1',
  transcript: { text: 'hello', language: null },
  answer: { text: 'hi', sources: [{ id: 's', title: 'Docs', url: null, kind: 'documentation' }] },
};

describe('QuestionsApi', () => {
  let http: HttpTestingController;
  let token: string | null;

  beforeEach(() => {
    token = 'jwt-123';
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthTokenProvider, useValue: { getToken: () => token } },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });

  it('POSTs multipart with the audio field and bearer token', () => {
    let result: QuestionResponse | undefined;
    TestBed.inject(QuestionsApi)
      .ask(new Blob(['x'], { type: 'audio/webm' }))
      .subscribe((r) => (result = r));

    const req = http.expectOne('/v1/questions');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toBeInstanceOf(FormData);
    expect((req.request.body as FormData).get('audio')).toBeInstanceOf(Blob);
    expect(req.request.headers.get('Authorization')).toBe('Bearer jwt-123');
    req.flush(OK);
    expect(result).toEqual(OK);
  });

  it('omits Authorization when there is no token', () => {
    token = null;
    TestBed.inject(QuestionsApi).ask(new Blob(['x'])).subscribe();
    const req = http.expectOne('/v1/questions');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush(OK);
  });

  it('maps RFC 9457 problem+json errors to ApiProblemError', () => {
    let error: unknown;
    TestBed.inject(QuestionsApi)
      .ask(new Blob(['x']))
      .subscribe({ error: (e: unknown) => (error = e) });
    http.expectOne('/v1/questions').flush(
      { type: 'urn:problem:stt', title: 'Unprocessable audio', status: 422, detail: 'Too short' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    expect(error).toBeInstanceOf(ApiProblemError);
    expect((error as ApiProblemError).problem).toMatchObject({ status: 422, title: 'Unprocessable audio', detail: 'Too short' });
  });

  it('falls back to a generic problem for non-problem failures', () => {
    let error: unknown;
    TestBed.inject(QuestionsApi)
      .ask(new Blob(['x']))
      .subscribe({ error: (e: unknown) => (error = e) });
    http.expectOne('/v1/questions').error(new ProgressEvent('error'), { status: 0, statusText: '' });
    expect(error).toBeInstanceOf(ApiProblemError);
    expect((error as ApiProblemError).problem.status).toBe(0);
  });
});
