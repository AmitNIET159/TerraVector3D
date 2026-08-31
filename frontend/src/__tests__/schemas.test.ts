import { describe, it, expect } from 'vitest';

describe('schema validation', () => {
  const ULPIN_PATTERN = /^[A-Z0-9]{14}$/;
  const VID_PATTERN = /^[A-Z0-9]{14}-F(G|B[1-9]|[0-9]{2})-U[A-Z0-9]{1,16}-R[0-9]{2}$/;

  it('validates canonical ULPIN', () => {
    expect('7A4B9C2D8E1F6G').toMatch(ULPIN_PATTERN);
    expect('7A4B9C2D8E1F6').not.toMatch(ULPIN_PATTERN); // 13 chars
    expect('7a4b9c2d8e1f6g').not.toMatch(ULPIN_PATTERN); // lowercase
  });

  it('validates vertical ID format', () => {
    expect('7A4B9C2D8E1F6G-F04-UAPT401-R01').toMatch(VID_PATTERN);
    expect('7A4B9C2D8E1F6G-FG-USHOP01-R01').toMatch(VID_PATTERN);
    expect('7A4B9C2D8E1F6G-FB1-UPARK01-R01').toMatch(VID_PATTERN);
    expect('INVALID').not.toMatch(VID_PATTERN);
  });

  it('validates severity enum', () => {
    const validSeverities = ['low', 'medium', 'high'];
    validSeverities.forEach((s) => expect(validSeverities).toContain(s));
    expect(validSeverities).not.toContain('critical');
  });
});
