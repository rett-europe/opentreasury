import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { Tag, TagCreate } from '@shared/models/tag.model';

@Injectable({ providedIn: 'root' })
export class TagService {
  private readonly api = inject(ApiService);

  list(): Observable<Tag[]> {
    return this.api.get<Tag[]>('/tags');
  }

  get(id: string): Observable<Tag> {
    return this.api.get<Tag>(`/tags/${id}`);
  }

  create(tag: TagCreate): Observable<Tag> {
    return this.api.post<Tag>('/tags', tag);
  }

  update(id: string, tag: Partial<TagCreate>): Observable<Tag> {
    return this.api.put<Tag>(`/tags/${id}`, tag);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`/tags/${id}`);
  }
}
