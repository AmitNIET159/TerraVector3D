import client from './client';
import type {
  HealthResponse,
  Parcel,
  Building,
  SpatialUnit,
  IdentityGenerateRequest,
  IdentityGenerateResponse,
  IdentityValidateRequest,
  IdentityValidateResponse,
  RightsValidateRequest,
  RightsValidateResponse,
  TopologyValidateRequest,
  TopologyValidateResponse,
  GeospatialFloorsResponse,
  ReportGenerateResponse,
} from '@/types';

export const getHealth = () => client.get<HealthResponse>('/health').then((r) => r.data);
export const getParcels = () => client.get<Parcel[]>('/api/v1/parcels').then((r) => r.data);
export const getParcel = (ulpin: string) => client.get<Parcel>(`/api/v1/parcels/${ulpin}`).then((r) => r.data);
export const getBuilding = (id: string) => client.get<Building>(`/api/v1/buildings/${id}`).then((r) => r.data);
export const getSpatialUnit = (id: string) => client.get<SpatialUnit>(`/api/v1/spatial-units/${id}`).then((r) => r.data);

export const generateIdentity = (req: IdentityGenerateRequest) =>
  client.post<IdentityGenerateResponse>('/api/v1/identity/generate', req).then((r) => r.data);
export const validateIdentity = (req: IdentityValidateRequest) =>
  client.post<IdentityValidateResponse>('/api/v1/identity/validate', req).then((r) => r.data);
export const validateRights = (req: RightsValidateRequest) =>
  client.post<RightsValidateResponse>('/api/v1/rights/validate', req).then((r) => r.data);
export const validateTopology = (req: TopologyValidateRequest) =>
  client.post<TopologyValidateResponse>('/api/v1/topology/validate', req).then((r) => r.data);
export const detectFloors = (pointCloud: number[][], tolerance = 0.5) =>
  client.post<GeospatialFloorsResponse>('/api/v1/geospatial/floors', {
    point_cloud_data: pointCloud, merge_tolerance_m: tolerance,
  }).then((r) => r.data);
export const generateReport = (validationData: Record<string, unknown>) =>
  client.post<ReportGenerateResponse>('/api/v1/reports/generate', {
    validation_data: validationData,
  }).then((r) => r.data);
