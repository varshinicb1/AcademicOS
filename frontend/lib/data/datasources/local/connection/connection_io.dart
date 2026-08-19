import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';

LazyDatabase openConnection(String dbPath) {
  return LazyDatabase(() async {
    final file = File(dbPath);
    return NativeDatabase.createInBackground(file);
  });
}
