// Tag — matches Cosmos DB reference_data container (type: "tag")
export interface Tag {
  id: string;
  type: string;
  name: string;
  color: string;
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string | null;
}

export interface TagCreate {
  name: string;
  color: string;
  sortOrder?: number;
  isActive?: boolean;
}
